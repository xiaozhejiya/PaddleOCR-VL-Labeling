from __future__ import annotations

from fastapi import Response

from app.api.v1.endpoints import auth as auth_endpoint


class DummyDb:
    def __init__(self, user: object | None):
        self._user = user

    def scalar(self, _stmt: object):
        return self._user


def test_login_sets_http_only_auth_cookie(monkeypatch) -> None:
    user = type(
        "User",
        (),
        {
            "id": 1,
            "username": "annotator",
            "display_name": "标注员",
            "password_hash": "hashed",
            "status": "active",
            "deleted_at": None,
            "is_system_admin": False,
        },
    )()
    db = DummyDb(user=user)
    response = Response()

    monkeypatch.setattr(auth_endpoint, "verify_password", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(auth_endpoint, "create_access_token", lambda **_kwargs: "cookie-token")
    monkeypatch.setattr(
        auth_endpoint,
        "get_settings",
        lambda: type("Settings", (), {"jwt_expire_minutes": 60})(),
    )

    result = auth_endpoint.login(
        payload=auth_endpoint.LoginRequest(username="annotator", password="password"),
        response=response,
        db=db,
    )

    assert result.user.username == "annotator"
    set_cookie = response.headers.get("set-cookie", "")
    assert "k12_access_token=cookie-token" in set_cookie
    assert "HttpOnly" in set_cookie


def test_logout_clears_auth_cookie() -> None:
    response = Response()

    result = auth_endpoint.logout(response=response)

    assert result.status_code == 204
    set_cookie = response.headers.get("set-cookie", "")
    assert "k12_access_token=" in set_cookie
    assert "Max-Age=0" in set_cookie or "expires=" in set_cookie.lower()
