from __future__ import annotations

from typing import Any

from sqlalchemy import delete, desc, func, select
from sqlalchemy.orm import Session

from app.db.models import (
    AnnotationObject,
    AnnotationRevision,
    Asset,
    AuditLog,
    Document,
    Page,
    RelationObject,
)
from app.storage.annotation_json import StoredJsonAsset


class SqlAlchemyAnnotationRepository:
    def get_page_context_by_public_id(
        self, db: Session, page_public_id: str
    ) -> dict[str, Any] | None:
        stmt = (
            select(Page, Document, Asset)
            .join(Document, Document.id == Page.document_id)
            .outerjoin(Asset, Asset.id == Page.image_asset_id)
            .where(Page.public_id == page_public_id)
        )
        row = db.execute(stmt).first()
        if row is None:
            return None
        page, document, image_asset = row
        return {
            "page_id": page.id,
            "page_public_id": page.public_id,
            "page_index": page.page_index,
            "document_id": document.id,
            "document_public_id": document.public_id,
            "project_id": document.project_id,
            "width": page.width,
            "height": page.height,
            "status": page.status,
            "capture_method": page.capture_method,
            "visual_difficulty": page.visual_difficulty,
            "image_asset_id": page.image_asset_id,
            "image_asset_public_id": image_asset.public_id if image_asset else None,
            "image_sha256": image_asset.sha256 if image_asset else None,
        }

    def get_latest_revision_no(self, db: Session, *, page_id: int) -> int:
        stmt = (
            select(AnnotationRevision.revision_no)
            .where(AnnotationRevision.page_id == page_id)
            .order_by(desc(AnnotationRevision.revision_no))
            .limit(1)
        )
        return db.scalar(stmt) or 0

    def get_latest_revision(
        self, db: Session, *, page_public_id: str
    ) -> AnnotationRevision | None:
        stmt = (
            select(AnnotationRevision)
            .join(Page, Page.id == AnnotationRevision.page_id)
            .where(Page.public_id == page_public_id)
            .order_by(desc(AnnotationRevision.revision_no))
            .limit(1)
        )
        return db.scalar(stmt)

    def get_revision_by_public_id(
        self, db: Session, *, revision_public_id: str
    ) -> AnnotationRevision | None:
        stmt = select(AnnotationRevision).where(
            AnnotationRevision.public_id == revision_public_id
        )
        return db.scalar(stmt)

    def get_revision_asset(
        self, db: Session, *, revision: AnnotationRevision
    ) -> Asset | None:
        return db.get(Asset, revision.annotation_json_asset_id)

    def list_revisions(
        self,
        db: Session,
        *,
        page_public_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AnnotationRevision], int]:
        count_stmt = (
            select(func.count())
            .select_from(AnnotationRevision)
            .join(Page, Page.id == AnnotationRevision.page_id)
            .where(Page.public_id == page_public_id)
        )
        total = int(db.scalar(count_stmt) or 0)

        stmt = (
            select(AnnotationRevision)
            .join(Page, Page.id == AnnotationRevision.page_id)
            .where(Page.public_id == page_public_id)
            .order_by(desc(AnnotationRevision.revision_no))
            .limit(limit)
            .offset(offset)
        )
        rows = db.scalars(stmt).all()
        return rows, total

    def create_revision(
        self,
        db: Session,
        *,
        public_id: str,
        project_id: int,
        document_id: int,
        page_id: int,
        revision_no: int,
        parent_revision_id: int | None,
        annotation_json_asset: StoredJsonAsset,
        created_by: int,
        change_summary: str | None,
        change_reason: str | None,
    ) -> AnnotationRevision:
        asset = Asset(
            public_id=annotation_json_asset.public_id,
            asset_type="annotation_json",
            storage_path=annotation_json_asset.storage_path,
            original_filename=f"{public_id}.json",
            mime_type="application/json",
            size_bytes=annotation_json_asset.size_bytes,
            sha256=annotation_json_asset.sha256,
            created_by=created_by,
            readonly=True,
        )
        db.add(asset)
        db.flush()

        revision = AnnotationRevision(
            public_id=public_id,
            project_id=project_id,
            document_id=document_id,
            page_id=page_id,
            revision_no=revision_no,
            parent_revision_id=parent_revision_id,
            annotation_json_asset_id=asset.id,
            status="draft",
            qc_status="pending",
            created_by=created_by,
            change_summary=change_summary,
            change_reason=change_reason,
        )
        db.add(revision)
        db.flush()
        db.add(
            AuditLog(
                project_id=project_id,
                actor_id=created_by,
                action="annotation_revision.create",
                resource_type="annotation_revision",
                resource_id=public_id,
                after_json={
                    "revision_id": public_id,
                    "page_internal_id": page_id,
                    "revision_no": revision_no,
                    "annotation_json_asset_id": asset.public_id,
                },
            )
        )
        return revision

    def rebuild_indexes(
        self,
        db: Session,
        *,
        revision_public_id: str,
        annotation_objects: list[dict[str, Any]],
        relation_objects: list[dict[str, Any]],
    ) -> None:
        revision = db.scalar(
            select(AnnotationRevision).where(
                AnnotationRevision.public_id == revision_public_id
            )
        )
        if revision is None:
            raise ValueError(f"标注版本不存在：{revision_public_id}")

        db.execute(
            delete(RelationObject).where(RelationObject.revision_id == revision.id)
        )
        db.execute(
            delete(AnnotationObject).where(AnnotationObject.revision_id == revision.id)
        )
        for item in annotation_objects:
            db.add(AnnotationObject(revision_id=revision.id, **item))
        db.flush()
        for item in relation_objects:
            db.add(RelationObject(revision_id=revision.id, **item))
        db.flush()
