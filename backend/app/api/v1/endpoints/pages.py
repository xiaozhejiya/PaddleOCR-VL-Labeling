from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_current_user
from app.db.models import User
from app.db.models.annotation import AnnotationRevision
from app.db.models.asset import Asset
from app.db.models.document import Document
from app.db.models.page import Page
from app.db.models.project import Project
from app.db.models.qc import QcResult
from app.db.session import get_db_session
from app.schemas.page import PageListOut, PageOut

router = APIRouter(prefix="/pages", tags=["pages"])


def _resolve_page(db: Session, page_public_id: str, current_user: User) -> tuple[Page, Document, Project]:
    """解析页面并校验用户权限，返回 (page, document, project)。"""
    page = db.scalar(select(Page).where(Page.public_id == page_public_id))
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
    doc = db.get(Document, page.document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    project = db.get(Project, doc.project_id)
    if not project or project.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return page, doc, project


# ── 页面详情 ──


@router.get("/{page_public_id}", response_model=PageOut, summary="获取页面详情")
def get_page(
    page_public_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> PageOut:
    page, doc, project = _resolve_page(db, page_public_id, current_user)
    filename = (doc.domain_metadata_json or {}).get("original_filename") or f"page-{page.public_id}"
    return PageOut(
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


@router.delete("/{page_public_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除页面")
def delete_page(
    page_public_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> None:
    page, doc, _project = _resolve_page(db, page_public_id, current_user)

    # 删除页面记录
    db.delete(page)
    db.flush()

    # 删除关联的文档记录
    db.delete(doc)
    db.commit()


# ── 页面图片 ──


@router.get("/{page_public_id}/image", summary="获取页面图片访问 URL")
def get_page_image_url(
    page_public_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    page, _doc, _project = _resolve_page(db, page_public_id, current_user)
    if not page.image_asset_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page has no image asset")

    asset = db.get(Asset, page.image_asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    return {
        "url": f"/api/v1/pages/{page_public_id}/image/raw",
        "expires_at": "9999-12-31T23:59:59Z",
    }


@router.get("/{page_public_id}/image/raw", summary="获取页面图片文件")
def get_page_image_raw(
    page_public_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    page, _doc, _project = _resolve_page(db, page_public_id, current_user)
    if not page.image_asset_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page has no image asset")

    asset = db.get(Asset, page.image_asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    settings = get_settings()
    file_path = Path(settings.storage_root) / asset.storage_path
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image file not found on disk")

    media_type = asset.mime_type or "application/octet-stream"
    return FileResponse(path=str(file_path), media_type=media_type)


# ── 标注 ──


@router.get("/{page_public_id}/annotations/latest", summary="获取页面最新标注")
def get_latest_annotation(
    page_public_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    page, _doc, _project = _resolve_page(db, page_public_id, current_user)

    rev = db.scalar(
        select(AnnotationRevision)
        .where(AnnotationRevision.page_id == page.id)
        .order_by(AnnotationRevision.revision_no.desc())
        .limit(1)
    )
    # 新页面没有标注时返回空结构，而不是 404
    if not rev:
        return {
            "id": None,
            "page_id": page.public_id,
            "revision_no": 0,
            "base_revision_id": None,
            "created_at": None,
            "created_by": None,
            "data": {"objects": []},
        }

    # 读取标注 JSON 资产内容
    ann_asset = db.get(Asset, rev.annotation_json_asset_id)
    ann_data: dict = {}
    if ann_asset:
        settings = get_settings()
        ann_path = Path(settings.storage_root) / ann_asset.storage_path
        if ann_path.exists():
            import json
            ann_data = json.loads(ann_path.read_text(encoding="utf-8"))

    return {
        "id": rev.public_id,
        "page_id": page.public_id,
        "revision_no": rev.revision_no,
        "base_revision_id": None,
        "created_at": rev.created_at.isoformat() if rev.created_at else None,
        "created_by": str(rev.created_by) if rev.created_by else None,
        "data": ann_data,
    }


# ── QC ──


@router.get("/{page_public_id}/qc", summary="获取页面 QC 问题列表")
def list_page_qc(
    page_public_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    page, _doc, _project = _resolve_page(db, page_public_id, current_user)

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


# ── 项目级页面列表（挂载在 projects 路由下，见 projects.py） ──


def list_project_pages(
    project_id: int,
    db: Session,
    current_user: User,
) -> PageListOut:
    """被 projects router 调用的内部函数：获取项目下所有页面。"""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

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
