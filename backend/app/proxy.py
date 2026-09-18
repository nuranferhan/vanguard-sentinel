import time
import httpx
from fastapi import Request
from app.config import settings
from app.security.rate_limiter import rate_limiter
from app.security.blacklist import blacklist_manager
from app.security.replay_guard import replay_guard
from app.security.geoip_filter import geoip_filter
from app.ai.ensemble import anomaly_ensemble
from app.ai.feature_store import feature_store
from app.admin.rule_engine import rule_engine
from app.models.schemas import TrafficEvent, ActionType, Protocol
from app.websocket.broadcaster import stats_broadcaster
from app.observability.metrics import (
    REQUEST_COUNTER,
    BLOCKED_REQUESTS_COUNTER,
    ANOMALY_SCORE_GAUGE,
    AUTOENCODER_ERROR_GAUGE,
)
from app.observability.alerting import alert_manager
from app.observability.event_stream import event_stream_producer
from app.observability.tracing import tracer
from app.admin.reports import report_generator
from app.ai.online_trainer import online_retrainer
from app.utils.logger import logger

_http_client = httpx.AsyncClient(base_url=settings.upstream_game_server, timeout=5.0)


class GatewayProxy:
    async def handle_request(self, request: Request) -> tuple[int, dict, bytes]:
        with tracer.start_as_current_span("gateway.handle_request"):
            client_ip = request.client.host
            endpoint = request.url.path.removeprefix("/gateway")
            body = await request.body()
            packet_size = len(body)

            online_retrainer.track_client(client_ip)

            if await blacklist_manager.is_banned(client_ip):
                return await self._reject(client_ip, endpoint, packet_size, ActionType.BLACKLISTED, 403)

            allowed_geo, country_code = geoip_filter.is_allowed(client_ip)
            if not allowed_geo:
                return await self._reject(
                    client_ip, endpoint, packet_size, ActionType.GEO_BLOCKED, 403, country_code
                )

            matched_rules = await rule_engine.match_rules(endpoint, country_code)
            for rule in matched_rules:
                if rule.max_requests_per_sec is not None:
                    allowed, _ = await rate_limiter.allow(client_ip, capacity_override=rule.max_requests_per_sec)
                    if not allowed:
                        return await self._reject(
                            client_ip, endpoint, packet_size, ActionType.RATE_LIMITED, 429, country_code
                        )
                if country_code in rule.blocked_countries:
                    return await self._reject(
                        client_ip, endpoint, packet_size, ActionType.GEO_BLOCKED, 403, country_code
                    )

            nonce = request.headers.get("X-Nonce")
            client_id = request.headers.get("X-Client-Id", client_ip)
            timestamp_header = request.headers.get("X-Timestamp")
            if nonce and timestamp_header:
                replay_result = await replay_guard.validate(client_id, nonce, float(timestamp_header))
                if not replay_result.is_valid:
                    return await self._reject(
                        client_ip, endpoint, packet_size, ActionType.REPLAY_BLOCKED, 403, country_code
                    )

            allowed, _ = await rate_limiter.allow(client_ip)
            if not allowed:
                banned = await blacklist_manager.record_violation(client_ip, "rate_limit_exceeded")
                status = 403 if banned else 429
                return await self._reject(
                    client_ip, endpoint, packet_size, ActionType.RATE_LIMITED, status, country_code
                )

            ensemble_result = anomaly_ensemble.evaluate(client_ip, endpoint, packet_size)
            ANOMALY_SCORE_GAUGE.set(ensemble_result.isolation_forest_score)
            AUTOENCODER_ERROR_GAUGE.set(ensemble_result.autoencoder_error)

            await feature_store.append(
                client_id,
                requests_per_sec=await rate_limiter.current_rate(client_ip),
                avg_packet_size=float(packet_size),
                unique_endpoints=1,
                interval_variance=0.0,
            )

            if ensemble_result.is_anomaly:
                banned = await blacklist_manager.record_violation(client_ip, "anomaly_detected")
                status = 403 if banned else 429
                return await self._reject(
                    client_ip, endpoint, packet_size, ActionType.ANOMALY_BLOCKED, status, country_code,
                    ensemble_result.isolation_forest_score, ensemble_result.autoencoder_error, ensemble_result.votes,
                )

            try:
                upstream_response = await _http_client.request(
                    method=request.method,
                    url=endpoint,
                    content=body,
                    headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                )
            except httpx.RequestError as exc:
                logger.error(f"Upstream erişilemedi: {exc}")
                return 502, {"error": f"Upstream unreachable: {exc}"}, b""

            await self._emit_event(
                client_ip, endpoint, packet_size, ActionType.ALLOWED, country_code,
                ensemble_result.isolation_forest_score, ensemble_result.autoencoder_error, ensemble_result.votes,
            )
            return upstream_response.status_code, dict(upstream_response.headers), upstream_response.content

    async def _reject(self, client_ip, endpoint, packet_size, action, status_code, country_code=None,
                       if_score=None, ae_error=None, votes=None):
        await self._emit_event(client_ip, endpoint, packet_size, action, country_code, if_score, ae_error, votes)
        BLOCKED_REQUESTS_COUNTER.labels(reason=action.value).inc()
        alert_manager.record_block()
        return status_code, {"error": action.value}, b""

    async def _emit_event(self, client_ip, endpoint, packet_size, action, country_code=None,
                           if_score=None, ae_error=None, votes=None):
        event = TrafficEvent(
            timestamp=time.time(),
            client_ip=client_ip,
            endpoint=endpoint,
            method="HTTP",
            packet_size=packet_size,
            action=action,
            protocol=Protocol.HTTP,
            anomaly_score=if_score,
            autoencoder_error=ae_error,
            ensemble_votes=votes,
            requests_last_window=int(await rate_limiter.current_rate(client_ip)),
            country_code=country_code,
        )
        REQUEST_COUNTER.labels(action=action.value, protocol="http").inc()
        await stats_broadcaster.broadcast(event.model_dump())
        await report_generator.record_event(event)
        await event_stream_producer.publish(event.model_dump())
        logger.info(f"{action.value} | ip={client_ip} | endpoint={endpoint} | country={country_code}")


gateway_proxy = GatewayProxy()
