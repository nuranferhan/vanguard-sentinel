import time
import hashlib
import hmac
import base64
import json
from app.config import settings
from app.models.schemas import Role, AdminUser

_DEMO_USERS: dict[str, dict] = {
    "admin": {"password_hash": hashlib.sha256(b"vanguard_admin_pw").hexdigest(), "role": Role.ADMIN},
    "analyst": {"password_hash": hashlib.sha256(b"vanguard_analyst_pw").hexdigest(), "role": Role.ANALYST},
    "viewer": {"password_hash": hashlib.sha256(b"vanguard_viewer_pw").hexdigest(), "role": Role.VIEWER},
}

ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {"read_stats", "manage_blacklist", "manage_rules", "view_audit_log", "manage_users"},
    Role.ANALYST: {"read_stats", "manage_blacklist", "view_audit_log"},
    Role.VIEWER: {"read_stats"},
}


class RBACService:


    def __init__(self, secret: str):
        self._secret = secret.encode()

    def authenticate(self, username: str, password: str) -> AdminUser | None:
        user = _DEMO_USERS.get(username)
        if user is None:
            return None
        if hmac.compare_digest(user["password_hash"], hashlib.sha256(password.encode()).hexdigest()):
            return AdminUser(username=username, role=user["role"])
        return None

    def issue_token(self, user: AdminUser) -> str:
        payload = json.dumps({"username": user.username, "role": user.role.value, "issued_at": time.time()})
        payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode()
        signature = hmac.new(self._secret, payload_b64.encode(), hashlib.sha256).hexdigest()
        return f"{payload_b64}.{signature}"

    def verify_token(self, token: str) -> AdminUser | None:
        try:
            payload_b64, signature = token.split(".")
            expected = hmac.new(self._secret, payload_b64.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, signature):
                return None
            data = json.loads(base64.urlsafe_b64decode(payload_b64))
            return AdminUser(username=data["username"], role=Role(data["role"]))
        except Exception:
            return None

    def has_permission(self, user: AdminUser, permission: str) -> bool:
        return permission in ROLE_PERMISSIONS.get(user.role, set())


rbac_service = RBACService(secret=settings.jwt_admin_secret)
