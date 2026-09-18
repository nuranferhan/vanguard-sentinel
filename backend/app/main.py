import time
import asyncio
import psutil
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.config import settings
from app.proxy import gateway_proxy
from app.security.blacklist import blacklist_manager
from app.security.rate_limiter import rate_limiter
from app.security.token_auth import token_authenticator
from app.websocket.broadcaster import stats_broadcaster
from app.models.schemas import ServerHealth, LoginRequest, TokenResponse, Role
from app.protocols.udp_gateway import start_udp_gateway
from app.protocols.ws_gateway import ws_game_gateway
from app.ai.online_trainer import online_retrainer
from app.admin.rbac import rbac_service
from app.admin.rule_engine import rule_engine
from app.admin.audit_log import audit_logger
from app.admin.reports import report_generator
from app.observability.metrics import render_metrics, ACTIVE_BLACKLIST_GAUGE, ACTIVE_WS_CONNECTIONS_GAUGE
from app.observability.event_stream import event_stream_producer
from app.utils.logger import logger

app = FastAPI(title=settings.app_name, version="7.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_permission(permission: str):
    async def dependency(authorization: str = Header(default="")):
        token = authorization.replace("Bearer ", "")
        user = rbac_service.verify_token(token)
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid or missing admin token")
        if not rbac_service.has_permission(user, permission):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/gateway"):
        token = request.headers.get("X-Session-Token")
        if not token or token_authenticator.verify_token(token) is None:
            return JSONResponse(status_code=401, content={"error": "Invalid or missing session token"})
    return await call_next(request)


@app.api_route("/gateway/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway_endpoint(full_path: str, request: Request):
    status_code, headers, content = await gateway_proxy.handle_request(request)
    return JSONResponse(status_code=status_code, content=None if not content else _safe_json(content))


def _safe_json(content: bytes):
    import json
    try:
        return json.loads(content)
    except Exception:
        return {"raw": content.decode(errors="ignore")}


@app.post("/auth/issue-token")
async def issue_token(client_id: str, session_id: str):
    token = token_authenticator.encrypt_token(client_id, session_id)
    return {"token": token}


@app.post("/admin/login", response_model=TokenResponse)
async def admin_login(payload: LoginRequest):
    user = rbac_service.authenticate(payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = rbac_service.issue_token(user)
    await audit_logger.record(actor=user.username, action="login", target="admin_panel")
    return TokenResponse(access_token=token, role=user.role)


@app.get("/admin/blacklist")
async def get_blacklist(user=Depends(require_permission("read_stats"))):
    return [entry.model_dump() for entry in await blacklist_manager.list_active()]


@app.post("/admin/blacklist/{ip}/ban")
async def ban_ip(ip: str, reason: str = "manual_ban", user=Depends(require_permission("manage_blacklist"))):
    await blacklist_manager.ban(ip, reason)
    await audit_logger.record(actor=user.username, action="ban_ip", target=ip, detail=reason)
    return {"status": "banned", "ip": ip}


@app.post("/admin/blacklist/{ip}/unban")
async def unban_ip(ip: str, user=Depends(require_permission("manage_blacklist"))):
    await blacklist_manager.unban(ip)
    await audit_logger.record(actor=user.username, action="unban_ip", target=ip)
    return {"status": "unbanned", "ip": ip}


@app.get("/admin/rules")
async def list_rules(user=Depends(require_permission("manage_rules"))):
    return [rule.model_dump() for rule in await rule_engine.list_rules()]


@app.post("/admin/rules")
async def create_rule(
    name: str,
    endpoint_pattern: str,
    max_requests_per_sec: int | None = None,
    user=Depends(require_permission("manage_rules")),
):
    rule = await rule_engine.create_rule(
        name=name,
        endpoint_pattern=endpoint_pattern,
        created_by=user.username,
        max_requests_per_sec=max_requests_per_sec,
    )
    await audit_logger.record(actor=user.username, action="create_rule", target=rule.rule_id, detail=name)
    return rule.model_dump()


@app.delete("/admin/rules/{rule_id}")
async def delete_rule(rule_id: str, user=Depends(require_permission("manage_rules"))):
    await rule_engine.delete_rule(rule_id)
    await audit_logger.record(actor=user.username, action="delete_rule", target=rule_id)
    return {"status": "deleted", "rule_id": rule_id}


@app.get("/admin/audit-log")
async def get_audit_log(limit: int = 100, user=Depends(require_permission("view_audit_log"))):
    return [entry.model_dump() for entry in await audit_logger.list_entries(limit)]


@app.get("/admin/reports/summary")
async def get_report_summary(days: float = 7, user=Depends(require_permission("read_stats"))):
    return await report_generator.generate_summary(since_seconds=days * 86400)


@app.get("/metrics")
async def metrics_endpoint():
    ACTIVE_BLACKLIST_GAUGE.set(len(await blacklist_manager.list_active()))
    ACTIVE_WS_CONNECTIONS_GAUGE.set(stats_broadcaster.connection_count)
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)


@app.websocket("/ws/stats")
async def stats_ws(websocket: WebSocket):
    await stats_broadcaster.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        stats_broadcaster.disconnect(websocket)


@app.websocket(settings.ws_gateway_path)
async def game_ws(websocket: WebSocket, token: str | None = None):
    await ws_game_gateway.handle_connection(websocket, token)


async def _health_loop():
    while True:
        active_blacklist = await blacklist_manager.list_active()
        health = ServerHealth(
            timestamp=time.time(),
            cpu_usage_percent=psutil.cpu_percent(),
            active_connections=stats_broadcaster.connection_count,
            upstream_latency_ms=0.0,
            requests_per_sec=0.0,
            blocked_last_minute=len(active_blacklist),
        )
        await stats_broadcaster.broadcast({"type": "health", "data": health.model_dump()})
        await asyncio.sleep(5)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(_health_loop())
    asyncio.create_task(start_udp_gateway())
    asyncio.create_task(online_retrainer.run_forever())
    await event_stream_producer.start()
    logger.info(f"{settings.app_name} başlatıldı")


@app.on_event("shutdown")
async def shutdown_event():
    await rate_limiter.close()
    await blacklist_manager.close()
    await event_stream_producer.stop()


@app.get("/")
async def root():
    return {"service": settings.app_name, "status": "operational", "version": "7.0.0"}
