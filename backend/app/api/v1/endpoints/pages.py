from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, Query, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import ensure_project_capability, get_current_user
from app.db.models import User
from app.db.models.asset import Asset
from app.db.models.document import Document
from app.db.models.page import Page
from app.db.models.project import Project
from app.db.models.qc import QcResult
from app.db.session import get_db_session
from app.schemas.annotation import (
    AnnotationRevisionReadData,
    AnnotationRevisionResponse,
)
from app.schemas.page import PageImageRead, PageListOut, PageOut, PageReadData, PageReadResponse
from app.services.annotation_service import (
    AnnotationRevisionNotFoundError,
    InvalidAnnotationError,
    PageNotFoundError,
    create_annotation_revision,
    get_annotation_revision,
    get_latest_annotation_revision,
    get_page_detail,
    RevisionConflictError,
)
from app.storage.local import StorageError
from app.utils.ids import new_public_id

router = APIRouter(tags=["pages"])


# ── 页面详情 ──


@router.get(
    "/pages/{page_id}",
    response_model=PageReadResponse,
    summary="获取页面详情",
)
def read_page(
    page_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    try:
        page = get_page_detail(db=db, page_public_id=page_id)
    except PageNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PAGE_NOT_FOUND",
            message=str(exc),
            details={"page_id": page_id},
        )
    ensure_project_capability(
        db,
        user_id=current_user.id,
        project_id=int(page["project_id"]),
        capability="can_view_project",
    )
    return PageReadResponse(data=_page_data(page), request_id=new_public_id("req"))


# ── 页面图片 ──


@router.get("/pages/{page_id}/image", summary="获取页面图片访问 URL", response_model=None)
def get_page_image_url(
    page_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    try:
        page_data = get_page_detail(db=db, page_public_id=page_id)
    except PageNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PAGE_NOT_FOUND",
            message=str(exc),
            details={"page_id": page_id},
        )
    ensure_project_capability(
        db,
        user_id=current_user.id,
        project_id=int(page_data["project_id"]),
        capability="can_view_project",
    )
    return {
        "url": f"/api/v1/pages/{page_id}/image/raw",
        "expires_at": "9999-12-31T23:59:59Z",
    }


@router.get("/pages/{page_id}/image/raw", summary="获取页面图片文件", response_model=None)
def get_page_image_raw(
    page_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    page = db.scalar(select(Page).where(Page.public_id == page_id))
    if not page:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PAGE_NOT_FOUND",
            message="Page not found",
            details={"page_id": page_id},
        )
    if not page.image_asset_id:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="IMAGE_NOT_FOUND",
            message="Page has no image asset",
            details={"page_id": page_id},
        )

    asset = db.get(Asset, page.image_asset_id)
    if not asset:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ASSET_NOT_FOUND",
            message="Asset not found",
            details={"page_id": page_id},
        )

    settings = get_settings()
    file_path = Path(settings.storage_root) / asset.storage_path
    if not file_path.exists():
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="FILE_NOT_FOUND",
            message="Image file not found on disk",
            details={"page_id": page_id},
        )

    return FileResponse(path=str(file_path), media_type=asset.mime_type or "application/octet-stream")


# ── 标注 ──


@router.get(
    "/pages/{page_id}/annotation/latest",
    response_model=AnnotationRevisionResponse,
    summary="读取页面最新标注版本",
)
def read_latest_annotation_revision(
    page_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    try:
        page = get_page_detail(db=db, page_public_id=page_id)
    except PageNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PAGE_NOT_FOUND",
            message=str(exc),
            details={"page_id": page_id},
        )
    ensure_project_capability(
        db,
        user_id=current_user.id,
        project_id=int(page["project_id"]),
        capability="can_view_project",
    )
    try:
        result = get_latest_annotation_revision(db=db, page_public_id=page_id)
    except AnnotationRevisionNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ANNOTATION_REVISION_NOT_FOUND",
            message=str(exc),
            details={"page_id": page_id},
        )
    except StorageError as exc:
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="STORAGE_ERROR",
            message=str(exc),
            details={"page_id": page_id},
        )
    return AnnotationRevisionResponse(
        data=_revision_data(
            revision=result["revision"],
            asset=result["asset"],
            annotation_json=result["annotation_json"],
            page_id=page_id,
        ),
        request_id=new_public_id("req"),
    )


@router.post(
    "/pages/{page_id}/annotation/revisions",
    response_model=AnnotationRevisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建页面标注版本",
)
def create_page_annotation_revision(
    page_id: str,
    payload: dict[str, Any] = Body(
        ..., description="整页 annotation JSON 或包装后的提交请求。"
    ),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    try:
        page = get_page_detail(db=db, page_public_id=page_id)
    except PageNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PAGE_NOT_FOUND",
            message=str(exc),
            details={"page_id": page_id},
        )
    ensure_project_capability(
        db,
        user_id=current_user.id,
        project_id=int(page["project_id"]),
        capability="can_create_annotation_revision",
    )
    annotation_json, change_summary, change_reason, base_revision_id = (
        _extract_revision_payload(payload)
    )
    try:
        revision = create_annotation_revision(
            db=db,
            page_public_id=page_id,
            annotation_json=annotation_json,
            created_by=current_user.id,
            change_summary=change_summary,
            change_reason=change_reason,
            base_revision_id=base_revision_id,
        )
        result = get_annotation_revision(db=db, revision_public_id=revision.public_id)
    except InvalidAnnotationError as exc:
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
            details={"page_id": page_id},
        )
    except RevisionConflictError as exc:
        return _error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="REVISION_CONFLICT",
            message=str(exc),
            details={"page_id": page_id},
        )
    except PageNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PAGE_NOT_FOUND",
            message=str(exc),
            details={"page_id": page_id},
        )
    except StorageError as exc:
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="STORAGE_ERROR",
            message=str(exc),
            details={"page_id": page_id},
        )
    return AnnotationRevisionResponse(
        data=_revision_data(
            revision=revision,
            asset=result["asset"],
            annotation_json=result["annotation_json"],
            page_id=page_id,
        ),
        request_id=new_public_id("req"),
    )


# ── QC ──


@router.get("/pages/{page_id}/qc", summary="获取页面 QC 问题列表", response_model=None)
def list_page_qc(
    page_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    page = db.scalar(select(Page).where(Page.public_id == page_id))
    if not page:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PAGE_NOT_FOUND",
            message="Page not found",
            details={"page_id": page_id},
        )

    rows = db.scalars(
        select(QcResult)
        .where(QcResult.page_id == page.id)
        .order_by(QcResult.created_at.desc())
    ).all()

    items = []
    for r in rows:
        items.append({
            "id": str(r.id),
            "page_id": page.public_id,
            "annotation_id": None,
            "severity": r.status,
            "code": r.qc_type,
            "message": r.summary or "",
            "details": r.details_json,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return {"items": items, "total": len(items)}


# ── 项目级页面列表 ──


def list_project_pages(
    project_id: int,
    db: Session,
    current_user: User,
) -> PageListOut:
    """被 projects router 调用的内部函数：获取项目下所有页面。"""
    project = db.get(Project, project_id)
    if not project:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PROJECT_NOT_FOUND",
            message="Project not found",
        )

    stmt = (
        select(Page, Document)
        .join(Document, Page.document_id == Document.id)
        .where(Document.project_id == project_id)
        .order_by(Page.created_at.desc())
    )
    rows = db.execute(stmt).all()

    items = []
    for page, doc in rows:
        filename = (doc.domain_metadata_json or {}).get("original_filename") or f"page-{page.public_id}"
        items.append(
            PageOut(
                id=page.id,
                page_id=page.public_id,
                project_id=doc.project_id,
                filename=filename,
                status=page.status,
                width=page.width,
                height=page.height,
                created_at=page.created_at,
                updated_at=page.updated_at,
            )
        )

    return PageListOut(items=items, total=len(items))


# ── 内部工具函数 ──


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            },
            "request_id": new_public_id("req"),
        },
    )


def _extract_revision_payload(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], str | None, str | None, str | None]:
    annotation_json = payload.get("annotation_json")
    if isinstance(annotation_json, dict):
        return (
            annotation_json,
            _optional_text(payload.get("change_summary")),
            _optional_text(payload.get("change_reason")),
            _optional_text(payload.get("base_revision_id")),
        )
    return payload, None, None, None


def _optional_text(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _page_data(page: dict[str, Any]) -> PageReadData:
    return PageReadData(
        page_id=page["page_public_id"],
        document_id=page["document_public_id"],
        project_id=page["project_id"],
        page_index=page["page_index"],
        status=page["status"],
        capture_method=page.get("capture_method"),
        visual_difficulty=page.get("visual_difficulty"),
        image=PageImageRead(
            asset_id=page.get("image_asset_public_id"),
            width=page["width"],
            height=page["height"],
            sha256=page.get("image_sha256"),
        ),
    )


def _revision_data(
    *,
    revision: Any,
    asset: Any,
    annotation_json: dict[str, Any],
    page_id: str,
) -> AnnotationRevisionReadData:
    return AnnotationRevisionReadData(
        revision_id=revision.public_id,
        page_id=page_id,
        revision_no=revision.revision_no,
        status=revision.status,
        qc_status=revision.qc_status,
        sha256=getattr(asset, "sha256", None),
        size_bytes=getattr(asset, "size_bytes", None),
        annotation_json=annotation_json,
    )
