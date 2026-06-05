from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Asset, AuditLog, Document, Page, Project, User


def get_project_by_id(db: Session, project_id: int) -> Project | None:
    return db.get(Project, project_id)


def get_active_user_by_id(db: Session, user_id: int) -> User | None:
    stmt = select(User).where(
        User.id == user_id,
        User.status == "active",
        User.deleted_at.is_(None),
    )
    return db.scalar(stmt)


def get_asset_by_sha256(db: Session, sha256: str) -> Asset | None:
    stmt = select(Asset).where(Asset.sha256 == sha256, Asset.deleted_at.is_(None))
    return db.scalar(stmt)


def create_asset(
    db: Session,
    *,
    public_id: str,
    asset_type: str,
    storage_path: str,
    original_filename: str | None,
    mime_type: str,
    size_bytes: int,
    sha256: str,
    width: int,
    height: int,
    created_by: int | None,
) -> Asset:
    asset = Asset(
        public_id=public_id,
        asset_type=asset_type,
        storage_path=storage_path,
        original_filename=original_filename,
        mime_type=mime_type,
        size_bytes=size_bytes,
        sha256=sha256,
        width=width,
        height=height,
        created_by=created_by,
        readonly=True,
    )
    db.add(asset)
    db.flush()
    return asset


def create_document_for_upload(
    db: Session,
    *,
    public_id: str,
    project_id: int,
    source_asset_public_id: str,
    original_filename: str | None,
) -> Document:
    document = Document(
        public_id=public_id,
        project_id=project_id,
        document_type="uploaded_image",
        source_type="upload",
        domain_metadata_json={
            "source_asset_id": source_asset_public_id,
            "original_filename": original_filename,
        },
        split="train",
        lock_status="unlocked",
    )
    db.add(document)
    db.flush()
    return document


def create_page_for_upload(
    db: Session,
    *,
    public_id: str,
    document_id: int,
    image_asset_id: int,
    width: int,
    height: int,
) -> Page:
    page = Page(
        public_id=public_id,
        document_id=document_id,
        page_index=0,
        image_asset_id=image_asset_id,
        width=width,
        height=height,
        capture_method="upload",
        status="imported",
    )
    db.add(page)
    db.flush()
    return page


def write_upload_audit_log(
    db: Session,
    *,
    project_id: int,
    actor_id: int | None,
    asset: Asset,
    document: Document,
    page: Page,
    asset_reused: bool,
) -> None:
    db.add(
        AuditLog(
            project_id=project_id,
            actor_id=actor_id,
            action="asset.upload",
            resource_type="asset",
            resource_id=asset.public_id,
            after_json={
                "asset_id": asset.public_id,
                "document_id": document.public_id,
                "page_id": page.public_id,
                "sha256": asset.sha256,
                "asset_reused": asset_reused,
            },
        )
    )
