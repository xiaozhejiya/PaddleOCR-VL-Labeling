"""鉴权和 capability 测试。

覆盖事项：
1. 密码哈希、JWT 生成、过期和篡改签名拒绝。
2. 未携带 bearer token 时拒绝访问当前用户依赖。
3. 项目写操作必须以后端计算的 capability 为准，缺失能力返回 403。
"""

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core import security


def test_password_hash_verification() -> None:
    password_hash = security.hash_password("secret-password")

    assert security.verify_password("secret-password", password_hash)
    assert not security.verify_password("wrong-password", password_hash)


def test_access_token_round_trip(monkeypatch) -> None:
    monkeypatch.setattr(security, "get_jwt_secret_key", lambda: "unit-test-secret")

    token = security.create_access_token(user_id=123)
    payload = security.decode_access_token(token)

    assert payload["sub"] == "123"
    assert "exp" in payload
    assert "jti" in payload


def test_access_token_rejects_tampered_signature(monkeypatch) -> None:
    monkeypatch.setattr(security, "get_jwt_secret_key", lambda: "unit-test-secret")
    token = security.create_access_token(user_id=123)
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")

    with pytest.raises(HTTPException) as exc_info:
        security.decode_access_token(tampered)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid access token."


def test_access_token_rejects_expired_token(monkeypatch) -> None:
    class ExpiredSettings:
        jwt_secret_key = "unit-test-secret"
        jwt_expire_minutes = -1

    monkeypatch.setattr(security, "get_settings", lambda: ExpiredSettings())
    token = security.create_access_token(user_id=123)

    with pytest.raises(HTTPException) as exc_info:
        security.decode_access_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Access token expired."


def test_bearer_dependency_requires_authorization_header() -> None:
    app = FastAPI()

    @app.get("/me")
    def read_me(_user=Depends(security.get_current_user)) -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(app)

    response = client.get("/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authentication token."


def test_cookie_session_allows_access_without_bearer_header(monkeypatch) -> None:
    app = FastAPI()

    monkeypatch.setattr(security, "decode_access_token", lambda _token: {"sub": "123"})

    class DummyUser:
        id = 123
        username = "annotator"
        display_name = "标注员"
        status = "active"
        deleted_at = None

    class DummyDb:
        def scalar(self, _stmt: object):
            return DummyUser()

    app.dependency_overrides[security.get_db_session] = lambda: DummyDb()

    @app.get("/me")
    def read_me(_user=Depends(security.get_current_user)) -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(app)
    client.cookies.set("k12_access_token", "cookie-token")

    response = client.get("/me")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_bearer_header_allows_access_without_cookie(monkeypatch) -> None:
    app = FastAPI()
    seen: dict[str, str] = {}

    def fake_decode_access_token(token: str) -> dict[str, str]:
        seen["token"] = token
        return {"sub": "123"}

    monkeypatch.setattr(security, "decode_access_token", fake_decode_access_token)

    class DummyUser:
        id = 123
        username = "annotator"
        display_name = "标注员"
        status = "active"
        deleted_at = None

    class DummyDb:
        def scalar(self, _stmt: object):
            return DummyUser()

    app.dependency_overrides[security.get_db_session] = lambda: DummyDb()

    @app.get("/me")
    def read_me(_user=Depends(security.get_current_user)) -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(app)

    response = client.get("/me", headers={"Authorization": "Bearer bearer-token"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert seen["token"] == "bearer-token"


class CapabilitySession:
    def __init__(self, permissions: list[dict[str, list[str]]]) -> None:
        self.permissions = permissions

    def scalars(self, _stmt: object) -> list[dict[str, list[str]]]:
        return self.permissions

    def get(self, _model: object, _id: int):
        return None


def test_ensure_project_capability_denies_missing_capability() -> None:
    db = CapabilitySession([{"capabilities": ["can_view_project"]}])

    with pytest.raises(HTTPException) as exc_info:
        security.ensure_project_capability(
            db,  # type: ignore[arg-type]
            user_id=1,
            project_id=1,
            capability="can_upload_assets",
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Permission denied."


def test_ensure_project_capability_merges_active_role_capabilities() -> None:
    db = CapabilitySession(
        [
            {"capabilities": ["can_view_project"]},
            {"capabilities": ["can_upload_assets"]},
        ]
    )

    security.ensure_project_capability(
        db,  # type: ignore[arg-type]
        user_id=1,
        project_id=1,
        capability="can_upload_assets",
    )
