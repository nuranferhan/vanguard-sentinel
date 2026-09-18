from app.admin.rbac import RBACService
from app.models.schemas import Role


def test_authenticate_valid_user():
    service = RBACService(secret="test_secret")
    user = service.authenticate("admin", "vanguard_admin_pw")
    assert user is not None
    assert user.role == Role.ADMIN


def test_authenticate_invalid_password():
    service = RBACService(secret="test_secret")
    user = service.authenticate("admin", "wrong_password")
    assert user is None


def test_token_roundtrip_and_permissions():
    service = RBACService(secret="test_secret")
    user = service.authenticate("analyst", "vanguard_analyst_pw")
    token = service.issue_token(user)
    verified = service.verify_token(token)
    assert verified is not None
    assert verified.username == "analyst"
    assert service.has_permission(verified, "manage_blacklist") is True
    assert service.has_permission(verified, "manage_rules") is False
