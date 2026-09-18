from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ActionType(str, Enum):
    ALLOWED = "allowed"
    RATE_LIMITED = "rate_limited"
    BLACKLISTED = "blacklisted"
    ANOMALY_BLOCKED = "anomaly_blocked"
    AUTH_FAILED = "auth_failed"
    REPLAY_BLOCKED = "replay_blocked"
    GEO_BLOCKED = "geo_blocked"
    MTLS_REJECTED = "mtls_rejected"
    CHEAT_DETECTED = "cheat_detected"


class Protocol(str, Enum):
    HTTP = "http"
    WEBSOCKET = "websocket"
    UDP = "udp"


class Role(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class TrafficEvent(BaseModel):
    timestamp: float
    client_ip: str
    endpoint: str
    method: str
    packet_size: int
    action: ActionType
    protocol: Protocol = Protocol.HTTP
    anomaly_score: Optional[float] = None
    autoencoder_error: Optional[float] = None
    ensemble_votes: Optional[int] = None
    requests_last_window: int = 0
    country_code: Optional[str] = None


class ServerHealth(BaseModel):
    timestamp: float
    cpu_usage_percent: float
    active_connections: int
    upstream_latency_ms: float
    requests_per_sec: float
    blocked_last_minute: int


class ClientToken(BaseModel):
    client_id: str
    session_id: str
    issued_at: float
    signature: str


class BlacklistEntry(BaseModel):
    ip: str
    reason: str
    banned_at: float
    expires_at: float
    violation_count: int = Field(default=1)


class ReplayGuardResult(BaseModel):
    is_valid: bool
    reason: Optional[str] = None


class CheatSignal(BaseModel):
    client_id: str
    signal_type: str
    detail: str
    detected_at: float
    severity: str


class FilterRule(BaseModel):
    rule_id: str
    name: str
    endpoint_pattern: str
    max_requests_per_sec: Optional[int] = None
    blocked_countries: list[str] = Field(default_factory=list)
    enabled: bool = True
    created_by: str
    created_at: float


class AuditLogEntry(BaseModel):
    actor: str
    action: str
    target: str
    timestamp: float
    detail: Optional[str] = None


class AdminUser(BaseModel):
    username: str
    role: Role


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    role: Role
