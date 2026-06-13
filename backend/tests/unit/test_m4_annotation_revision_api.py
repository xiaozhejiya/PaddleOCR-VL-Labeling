"""M4 页面与标注 revision API 合同测试。

覆盖事项：
1. v1 router 必须注册页面详情和标注 revision 的四个 MVP 入口。
2. API path 中的 page_id 表示 pages.public_id，而不是数据库内部主键。
3. 后续实现 endpoint 时，业务行为由 service 测试覆盖；本文件先锁住路由合同。
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest
from fastapi import HTTPException, status

from app.api.v1.endpoints import pages as pages_endpoint
from app.db.models import User
from app.main import create_app
from app.services.annotation_service import (
    AnnotationRevisionNotFoundError,
    InvalidAnnotationError,
    PageNotFoundError,
    RevisionConflictError,
)


def route_methods_by_path() -> dict[str, set[str]]:
    app = create_app()
    result: dict[str, set[str]] = {}
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", None)
        if methods:
            result.setdefault(path, set()).update(set(methods))
    return result


def test_m4_page_and_annotation_revision_routes_are_registered() -> None:
    routes = route_methods_by_path()

    assert "/api/v1/pages/{page_id}" in routes
    assert "GET" in routes["/api/v1/pages/{page_id}"]
    assert "DELETE" in routes["/api/v1/pages/{page_id}"]

    assert "/api/v1/pages/{page_id}/image" in routes
    assert "GET" in routes["/api/v1/pages/{page_id}/image"]

    assert "/api/v1/pages/{page_id}/image/raw" in routes
    assert "GET" in routes["/api/v1/pages/{page_id}/image/raw"]

    assert "/api/v1/pages/{page_id}/annotation/latest" in routes
    assert "GET" in routes["/api/v1/pages/{page_id}/annotation/latest"]

    assert "/api/v1/pages/{page_id}/annotation/revisions" in routes
    assert "POST" in routes["/api/v1/pages/{page_id}/annotation/revisions"]

    assert "/api/v1/pages/{page_id}/annotation/revisions/{revision_id}" in routes
    assert "GET" in routes["/api/v1/pages/{page_id}/annotation/revisions/{revision_id}"]


def test_m4_routes_use_public_page_id_name() -> None:
    routes = route_methods_by_path()
    m4_paths = {
        "/api/v1/pages/{page_id}",
        "/api/v1/pages/{page_id}/image",
        "/api/v1/pages/{page_id}/image/raw",
        "/api/v1/pages/{page_id}/annotation/latest",
        "/api/v1/pages/{page_id}/annotation/revisions",
        "/api/v1/pages/{page_id}/annotation/revisions/{revision_id}",
    }

    assert m4_paths.issubset(routes)
    assert all("{page_id}" in path for path in m4_paths)
    assert all(
        "{id}" not in path and "{page_internal_id}" not in path for path in m4_paths
    )


def sample_page_context() -> dict[str, Any]:
    return {
        "page_id": 30,
        "page_public_id": "page_public_001",
        "page_index": 0,
        "document_id": 20,
        "document_public_id": "doc_public_001",
        "project_id": 10,
        "width": 200,
        "height": 300,
        "status": "imported",
        "capture_method": "upload",
        "visual_difficulty": "medium",
        "image_asset_public_id": "asset_image_001",
        "image_sha256": "a" * 64,
    }


def sample_revision_result() -> dict[str, Any]:
    revision = type(
        "RevisionRecord",
        (),
        {
            "public_id": "rev_public_001",
            "page_id": 30,
            "revision_no": 1,
            "status": "draft",
            "qc_status": "pending",
        },
    )()
    asset = type(
        "AssetRecord",
        (),
        {
            "sha256": "b" * 64,
            "size_bytes": 128,
        },
    )()
    return {
        "revision": revision,
        "asset": asset,
        "annotation_json": {
            "page_id": "page_public_001",
            "k12_annotations": [],
            "relations": [],
            "history": [{"revision_id": "rev_public_001", "revision_no": 1}],
        },
    }


def create_test_app(monkeypatch: Any):
    app = create_app()
    app.dependency_overrides[pages_endpoint.get_current_user] = lambda: User(
        id=99,
        username="annotator",
        display_name="标注员",
        status="active",
    )
    app.dependency_overrides[pages_endpoint.get_db_session] = lambda: object()
    monkeypatch.setattr(
        pages_endpoint,
        "ensure_project_capability",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        pages_endpoint,
        "get_page_detail",
        lambda **_kwargs: sample_page_context(),
    )
    return app


def request(app: Any, method: str, path: str, **kwargs: Any) -> httpx.Response:
    async def _send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(_send())


def assert_error_response(
    response: Any,
    *,
    status_code: int,
    code: str,
    message_contains: str,
) -> None:
    payload = response.json()

    assert response.status_code == status_code
    assert "detail" not in payload
    assert payload["error"]["code"] == code
    assert message_contains in payload["error"]["message"]
    assert isinstance(payload["error"]["details"], dict)
    assert payload["request_id"].startswith("req_")


def test_read_page_endpoint_returns_page_metadata(monkeypatch: Any) -> None:
    app = create_test_app(monkeypatch)

    response = request(app, "GET", "/api/v1/pages/page_public_001")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "page_id": "page_public_001",
        "document_id": "doc_public_001",
        "project_id": 10,
        "page_index": 0,
        "status": "imported",
        "capture_method": "upload",
        "visual_difficulty": "medium",
        "image": {
            "asset_id": "asset_image_001",
            "width": 200,
            "height": 300,
            "sha256": "a" * 64,
        },
    }


def test_read_page_endpoint_maps_missing_page_to_error_response(
    monkeypatch: Any,
) -> None:
    app = create_test_app(monkeypatch)
    monkeypatch.setattr(
        pages_endpoint,
        "get_page_detail",
        lambda **_kwargs: (_ for _ in ()).throw(
            PageNotFoundError("页面不存在：page_missing")
        ),
    )

    response = request(app, "GET", "/api/v1/pages/page_missing")

    assert_error_response(
        response,
        status_code=404,
        code="PAGE_NOT_FOUND",
        message_contains="页面不存在",
    )


def test_latest_annotation_endpoint_returns_null_when_page_has_no_revision(
    monkeypatch: Any,
) -> None:
    app = create_test_app(monkeypatch)
    monkeypatch.setattr(
        pages_endpoint,
        "get_latest_annotation_revision",
        lambda **_kwargs: (_ for _ in ()).throw(
            AnnotationRevisionNotFoundError("页面还没有标注版本：page_public_001")
        ),
    )

    response = request(app, "GET", "/api/v1/pages/page_public_001/annotation/latest")

    assert response.status_code == 200
    assert response.json()["data"] is None
    assert response.json()["request_id"].startswith("req_")


def test_specific_annotation_revision_endpoint_returns_revision(
    monkeypatch: Any,
) -> None:
    app = create_test_app(monkeypatch)
    monkeypatch.setattr(
        pages_endpoint,
        "get_annotation_revision",
        lambda **kwargs: (
            sample_revision_result()
            if kwargs["revision_public_id"] == "rev_public_001"
            else pytest.fail("应按 revision_id 读取指定 revision")
        ),
    )

    response = request(
        app, "GET", "/api/v1/pages/page_public_001/annotation/revisions/rev_public_001"
    )

    assert response.status_code == 200
    assert response.json()["data"]["revision_id"] == "rev_public_001"


def test_list_annotation_revisions_endpoint_returns_revision_list(
    monkeypatch: Any,
) -> None:
    app = create_test_app(monkeypatch)

    revision = type(
        "RevisionRecord",
        (),
        {
            "public_id": "rev_public_002",
            "page_id": 30,
            "revision_no": 2,
            "status": "draft",
            "qc_status": "pending",
            "created_at": None,
            "change_summary": "第二次保存",
        },
    )()

    monkeypatch.setattr(
        pages_endpoint,
        "list_annotation_revisions",
        lambda **kwargs: (
            (
                [revision]
                if kwargs["page_public_id"] == "page_public_001"
                else pytest.fail("应按 page_id 列出版本")
            ),
            1,
        ),
    )

    response = request(app, "GET", "/api/v1/pages/page_public_001/annotation/revisions")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["revision_id"] == "rev_public_002"
    assert payload["items"][0]["revision_no"] == 2
    assert payload["items"][0]["change_summary"] == "第二次保存"


def test_specific_annotation_revision_endpoint_maps_missing_revision_to_404(
    monkeypatch: Any,
) -> None:
    app = create_test_app(monkeypatch)
    monkeypatch.setattr(
        pages_endpoint,
        "get_annotation_revision",
        lambda **_kwargs: (_ for _ in ()).throw(
            AnnotationRevisionNotFoundError("标注版本不存在：rev_missing")
        ),
    )

    response = request(
        app, "GET", "/api/v1/pages/page_public_001/annotation/revisions/rev_missing"
    )

    assert_error_response(
        response,
        status_code=404,
        code="ANNOTATION_REVISION_NOT_FOUND",
        message_contains="标注版本不存在",
    )


def test_post_annotation_revision_endpoint_accepts_wrapped_payload(
    monkeypatch: Any,
) -> None:
    app = create_test_app(monkeypatch)
    captured: dict[str, Any] = {}

    def create_revision(**kwargs: Any) -> Any:
        captured.update(kwargs)
        return sample_revision_result()["revision"]

    monkeypatch.setattr(pages_endpoint, "create_annotation_revision", create_revision)
    monkeypatch.setattr(
        pages_endpoint,
        "get_annotation_revision",
        lambda **kwargs: (
            sample_revision_result()
            if kwargs["revision_public_id"] == "rev_public_001"
            else pytest.fail("POST 响应必须读取刚创建的 revision")
        ),
    )
    monkeypatch.setattr(
        pages_endpoint,
        "get_latest_annotation_revision",
        lambda **_kwargs: pytest.fail("POST 创建后不能重新读取 latest"),
    )

    response = request(
        app,
        "POST",
        "/api/v1/pages/page_public_001/annotation/revisions",
        json={
            "annotation_json": {
                "page_id": "page_public_001",
                "k12_annotations": [],
                "relations": [],
            },
            "change_summary": "首次标注",
            "change_reason": "验收测试",
            "base_revision_id": None,
        },
    )

    assert response.status_code == 201
    assert captured["page_public_id"] == "page_public_001"
    assert captured["annotation_json"]["page_id"] == "page_public_001"
    assert captured["change_summary"] == "首次标注"
    assert captured["change_reason"] == "验收测试"
    assert captured["base_revision_id"] is None
    assert response.json()["data"]["revision_no"] == 1


def test_post_annotation_revision_endpoint_maps_conflict_to_409(
    monkeypatch: Any,
) -> None:
    app = create_test_app(monkeypatch)
    monkeypatch.setattr(
        pages_endpoint,
        "create_annotation_revision",
        lambda **_kwargs: (_ for _ in ()).throw(
            RevisionConflictError("base_revision_id 不是当前 latest")
        ),
    )

    response = request(
        app,
        "POST",
        "/api/v1/pages/page_public_001/annotation/revisions",
        json={
            "annotation_json": {
                "page_id": "page_public_001",
                "k12_annotations": [],
                "relations": [],
            },
            "base_revision_id": "rev_old",
        },
    )

    assert_error_response(
        response,
        status_code=409,
        code="REVISION_CONFLICT",
        message_contains="base_revision_id",
    )


def test_post_annotation_revision_endpoint_maps_invalid_input_to_422(
    monkeypatch: Any,
) -> None:
    app = create_test_app(monkeypatch)
    monkeypatch.setattr(
        pages_endpoint,
        "create_annotation_revision",
        lambda **_kwargs: (_ for _ in ()).throw(
            InvalidAnnotationError("bbox 超出页面范围。")
        ),
    )

    response = request(
        app,
        "POST",
        "/api/v1/pages/page_public_001/annotation/revisions",
        json={"page_id": "page_public_001", "k12_annotations": []},
    )

    assert_error_response(
        response,
        status_code=422,
        code="VALIDATION_ERROR",
        message_contains="bbox",
    )


def test_post_annotation_revision_endpoint_requires_create_capability(
    monkeypatch: Any,
) -> None:
    app = create_test_app(monkeypatch)
    monkeypatch.setattr(
        pages_endpoint,
        "ensure_project_capability",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied.",
            )
        ),
    )
    monkeypatch.setattr(
        pages_endpoint,
        "create_annotation_revision",
        lambda **_kwargs: pytest.fail("权限不足时不能创建 revision"),
    )

    response = request(
        app,
        "POST",
        "/api/v1/pages/page_public_001/annotation/revisions",
        json={"page_id": "page_public_001", "k12_annotations": []},
    )

    assert response.status_code == 403
