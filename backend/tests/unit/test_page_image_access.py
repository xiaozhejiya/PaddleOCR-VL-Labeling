from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from fastapi.responses import FileResponse, JSONResponse

from app.api.v1.endpoints import pages as pages_endpoint
from app.db.models.asset import Asset


class DummyDb:
    def __init__(self, *, page: object | None = None, asset: object | None = None):
        self._page = page
        self._asset = asset

    def scalar(self, _stmt: object) -> object | None:
        return self._page

    def get(self, model: object, _id: object) -> object | None:
        if model is Asset:
            return self._asset
        return None


def parse_json_response(response: JSONResponse) -> dict:
    return json.loads(response.body.decode("utf-8"))


def test_get_page_image_url_returns_verifiable_signed_url(monkeypatch) -> None:
    monkeypatch.setattr(
        pages_endpoint,
        "get_page_detail",
        lambda **_kwargs: {"project_id": 10},
    )
    monkeypatch.setattr(
        pages_endpoint,
        "ensure_project_capability",
        lambda *_args, **_kwargs: None,
    )

    response = pages_endpoint.get_page_image_url(
        page_id="page_public_001",
        db=object(),
        current_user=type("User", (), {"id": 99})(),
    )

    parsed = urlparse(response["url"])
    query = parse_qs(parsed.query)
    exp = int(query["exp"][0])
    sig = query["sig"][0]

    assert parsed.path == "/api/v1/pages/page_public_001/image/raw"
    assert pages_endpoint._verify_page_image_url(
        page_id="page_public_001",
        exp=exp,
        sig=sig,
    )
    assert response["expires_at"].endswith("Z")


def test_get_page_image_raw_rejects_expired_signed_url() -> None:
    exp = int((datetime.now(UTC) - timedelta(seconds=1)).timestamp())
    sig = pages_endpoint._sign_page_image_url(page_id="page_public_001", exp=exp)

    response = pages_endpoint.get_page_image_raw(
        page_id="page_public_001",
        db=DummyDb(),
        exp=exp,
        sig=sig,
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 401
    payload = parse_json_response(response)
    assert payload["error"]["code"] == "IMAGE_URL_EXPIRED"


def test_get_page_image_raw_rejects_invalid_signature() -> None:
    exp = int((datetime.now(UTC) + timedelta(minutes=5)).timestamp())

    response = pages_endpoint.get_page_image_raw(
        page_id="page_public_001",
        db=DummyDb(),
        exp=exp,
        sig="invalid_signature",
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 401
    payload = parse_json_response(response)
    assert payload["error"]["code"] == "IMAGE_URL_EXPIRED"


def test_get_page_image_raw_returns_file_response_for_valid_signed_url(
    monkeypatch, tmp_path: Path
) -> None:
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"fake_png")

    page = type("PageRow", (), {"image_asset_id": 1})()
    asset = type(
        "AssetRow",
        (),
        {"storage_path": "page.png", "mime_type": "image/png"},
    )()
    db = DummyDb(page=page, asset=asset)
    exp = int((datetime.now(UTC) + timedelta(minutes=5)).timestamp())
    sig = pages_endpoint._sign_page_image_url(page_id="page_public_001", exp=exp)

    monkeypatch.setattr(
        pages_endpoint,
        "get_settings",
        lambda: type("Settings", (), {"storage_root": tmp_path})(),
    )

    response = pages_endpoint.get_page_image_raw(
        page_id="page_public_001",
        db=db,
        exp=exp,
        sig=sig,
    )

    assert isinstance(response, FileResponse)
    assert Path(response.path) == image_path
