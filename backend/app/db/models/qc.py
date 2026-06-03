from __future__ import annotations

from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class QcResult(TimestampMixin, Base):
    __tablename__ = "qc_results"
    __table_args__ = (
        ForeignKeyConstraint(
            ["document_id", "project_id"],
            ["documents.id", "documents.project_id"],
            name="fk_qc_results_document_project",
        ),
        ForeignKeyConstraint(
            ["page_id", "document_id"],
            ["pages.id", "pages.document_id"],
            name="fk_qc_results_page_document",
        ),
        ForeignKeyConstraint(
            ["revision_id", "page_id"],
            ["annotation_revisions.id", "annotation_revisions.page_id"],
            name="fk_qc_results_revision_page",
        ),
        CheckConstraint(
            "qc_type IN ('schema', 'geometry', 'k12_structure', 'dataset', 'export')",
            name="ck_qc_results_qc_type",
        ),
        CheckConstraint(
            "status IN ('passed', 'warning', 'failed')",
            name="ck_qc_results_status",
        ),
        CheckConstraint(
            "page_id IS NULL OR document_id IS NOT NULL",
            name="ck_qc_results_page_requires_document",
        ),
        CheckConstraint(
            "revision_id IS NULL OR page_id IS NOT NULL",
            name="ck_qc_results_revision_requires_page",
        ),
        CheckConstraint(
            "jsonb_typeof(details_json) = 'object'",
            name="ck_qc_results_details_json_object",
        ),
        Index("ix_qc_results_project_id", "project_id"),
        Index("ix_qc_results_revision_id", "revision_id"),
        Index("ix_qc_results_status", "status"),
        {"comment": "质检结果表：保存 schema、geometry、dataset、export 等 QC 结果。"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
        comment="内部主键。",
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", name="fk_qc_results_project_id_projects"),
        nullable=False,
        comment="项目内部主键，引用 projects.id。",
    )
    document_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("documents.id", name="fk_qc_results_document_id_documents"),
        comment="文档内部主键，引用 documents.id。",
    )
    page_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("pages.id", name="fk_qc_results_page_id_pages"),
        comment="页面内部主键：引用 pages.id；公开页面编号位于 pages.public_id。",
    )
    revision_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "annotation_revisions.id",
            name="fk_qc_results_revision_id_annotation_revisions",
        ),
        comment="标注版本内部主键，引用 annotation_revisions.id。",
    )
    qc_type: Mapped[str] = mapped_column(Text, nullable=False, comment="质检类型。")
    status: Mapped[str] = mapped_column(Text, nullable=False, comment="质检状态。")
    summary: Mapped[str | None] = mapped_column(Text, comment="质检摘要。")
    details_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="质检详情 JSON：保存 errors / warnings 等结构化明细。",
    )
    created_by_job_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "background_jobs.id",
            name="fk_qc_results_created_by_job_id_background_jobs",
        ),
        comment="产生该质检结果的后台任务，引用 background_jobs.id。",
    )
