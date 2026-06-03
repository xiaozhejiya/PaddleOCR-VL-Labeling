from __future__ import annotations

from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class AnnotationRevision(TimestampMixin, Base):
    __tablename__ = "annotation_revisions"
    __table_args__ = (
        UniqueConstraint("public_id", name="uq_annotation_revisions_public_id"),
        UniqueConstraint(
            "page_id",
            "revision_no",
            name="uq_annotation_revisions_page_revision_no",
        ),
        UniqueConstraint("id", "page_id", name="uq_annotation_revisions_id_page"),
        ForeignKeyConstraint(
            ["document_id", "project_id"],
            ["documents.id", "documents.project_id"],
            name="fk_annotation_revisions_document_project",
        ),
        ForeignKeyConstraint(
            ["page_id", "document_id"],
            ["pages.id", "pages.document_id"],
            name="fk_annotation_revisions_page_document",
        ),
        ForeignKeyConstraint(
            ["parent_revision_id", "page_id"],
            ["annotation_revisions.id", "annotation_revisions.page_id"],
            name="fk_annotation_revisions_parent_same_page",
        ),
        CheckConstraint("revision_no > 0", name="ck_annotation_revisions_revision_no"),
        CheckConstraint(
            "status IN ('draft', 'submitted', 'reviewed', 'locked', 'superseded')",
            name="ck_annotation_revisions_status",
        ),
        CheckConstraint(
            "qc_status IN ('pending', 'passed', 'failed', 'warning')",
            name="ck_annotation_revisions_qc_status",
        ),
        CheckConstraint(
            "btrim(public_id) <> ''",
            name="ck_annotation_revisions_public_id_not_blank",
        ),
        Index("ix_annotation_revisions_project_id", "project_id"),
        Index("ix_annotation_revisions_document_id", "document_id"),
        Index("ix_annotation_revisions_page_id", "page_id"),
        Index(
            "ix_annotation_revisions_page_status_revision_no",
            "page_id",
            "status",
            text("revision_no DESC"),
        ),
        {"comment": "标注版本表：保存每次页面标注提交形成的不可变版本记录。"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
        comment="内部主键。",
    )
    public_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="公开标注版本编号：用于 API、manifest、导出追踪和审计展示。",
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", name="fk_annotation_revisions_project_id_projects"),
        nullable=False,
        comment="项目内部主键，引用 projects.id。",
    )
    document_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "documents.id",
            name="fk_annotation_revisions_document_id_documents",
        ),
        nullable=False,
        comment="文档内部主键，引用 documents.id。",
    )
    page_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("pages.id", name="fk_annotation_revisions_page_id_pages"),
        nullable=False,
        comment="页面内部主键：引用 pages.id；公开页面编号位于 pages.public_id。",
    )
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False, comment="同一页面内递增版本号。")
    parent_revision_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "annotation_revisions.id",
            name="fk_annotation_revisions_parent_revision_id_annotation_revisions",
        ),
        comment="父版本内部主键。",
    )
    annotation_json_asset_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "assets.id",
            name="fk_annotation_revisions_annotation_json_asset_id_assets",
        ),
        nullable=False,
        comment="标注 JSON 资产：引用 assets.id，完整标注事实保存在文件系统。",
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'draft'"),
        comment="版本状态。",
    )
    qc_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'pending'"),
        comment="质检状态。",
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_annotation_revisions_created_by_users"),
        comment="创建人，引用 users.id。",
    )
    change_summary: Mapped[str | None] = mapped_column(Text, comment="变更摘要。")
    change_reason: Mapped[str | None] = mapped_column(Text, comment="变更原因。")


class AnnotationObject(TimestampMixin, Base):
    __tablename__ = "annotation_objects"
    __table_args__ = (
        UniqueConstraint(
            "revision_id",
            "ann_id",
            name="uq_annotation_objects_revision_ann",
        ),
        CheckConstraint(
            "read_order IS NULL OR read_order > 0",
            name="ck_annotation_objects_read_order",
        ),
        CheckConstraint(
            "status IN ('active', 'deleted')",
            name="ck_annotation_objects_status",
        ),
        CheckConstraint(
            "btrim(ann_id) <> ''",
            name="ck_annotation_objects_ann_id_not_blank",
        ),
        CheckConstraint(
            "btrim(label_namespace) <> ''",
            name="ck_annotation_objects_label_namespace_not_blank",
        ),
        CheckConstraint(
            "btrim(label_name) <> ''",
            name="ck_annotation_objects_label_name_not_blank",
        ),
        CheckConstraint(
            "bbox_xyxy IS NULL OR jsonb_typeof(bbox_xyxy) = 'array'",
            name="ck_annotation_objects_bbox_xyxy_json_array",
        ),
        CheckConstraint(
            "quad IS NULL OR jsonb_typeof(quad) = 'array'",
            name="ck_annotation_objects_quad_json_array",
        ),
        CheckConstraint(
            "polygon IS NULL OR jsonb_typeof(polygon) = 'array'",
            name="ck_annotation_objects_polygon_json_array",
        ),
        CheckConstraint(
            "jsonb_typeof(attributes_json) = 'object'",
            name="ck_annotation_objects_attributes_json_object",
        ),
        CheckConstraint(
            "jsonb_typeof(source_refs_json) = 'object'",
            name="ck_annotation_objects_source_refs_json_object",
        ),
        Index("ix_annotation_objects_revision_id", "revision_id"),
        Index("ix_annotation_objects_label", "label_namespace", "label_name"),
        Index("ix_annotation_objects_status", "status"),
        Index("ix_annotation_objects_read_order", "read_order"),
        {"comment": "标注对象索引表：从 annotation revision JSON 抽取，用于查询和导出前索引。"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
        comment="内部主键。",
    )
    revision_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "annotation_revisions.id",
            name="fk_annotation_objects_revision_id_annotation_revisions",
            ondelete="CASCADE",
        ),
        nullable=False,
        comment="标注版本内部主键，引用 annotation_revisions.id。",
    )
    ann_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="标注对象编号：来自 revision JSON，同一 revision 内唯一。",
    )
    label_namespace: Mapped[str] = mapped_column(Text, nullable=False, comment="标签命名空间。")
    label_name: Mapped[str] = mapped_column(Text, nullable=False, comment="标签名称。")
    bbox_xyxy: Mapped[list[Any] | None] = mapped_column(JSONB, comment="bbox 几何。")
    quad: Mapped[list[Any] | None] = mapped_column(JSONB, comment="四点几何。")
    polygon: Mapped[list[Any] | None] = mapped_column(JSONB, comment="多边形几何。")
    read_order: Mapped[int | None] = mapped_column(Integer, comment="阅读顺序索引：事实来源仍是 revision JSON。")
    attributes_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="标注对象属性 JSON。",
    )
    source_refs_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="来源引用 JSON。",
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'active'"),
        comment="对象状态。",
    )
