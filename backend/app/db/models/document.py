from __future__ import annotations

from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Identity,
    Index,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class Document(TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("public_id", name="uq_documents_public_id"),
        UniqueConstraint("id", "project_id", name="uq_documents_id_project"),
        CheckConstraint(
            "split IN ('train', 'val', 'eval', 'external_auxiliary')",
            name="ck_documents_split",
        ),
        CheckConstraint(
            "lock_status IN ('unlocked', 'locked')",
            name="ck_documents_lock_status",
        ),
        CheckConstraint(
            "btrim(public_id) <> ''",
            name="ck_documents_public_id_not_blank",
        ),
        CheckConstraint(
            "btrim(document_type) <> ''",
            name="ck_documents_document_type_not_blank",
        ),
        CheckConstraint(
            "jsonb_typeof(domain_metadata_json) = 'object'",
            name="ck_documents_domain_metadata_json_object",
        ),
        Index(
            "uq_documents_project_document_code",
            "project_id",
            "document_code",
            unique=True,
            postgresql_where=text("document_code IS NOT NULL"),
        ),
        Index("ix_documents_project_id", "project_id"),
        Index("ix_documents_split", "split"),
        {"comment": "文档表：保存原始试卷、PDF 或其他文档级元数据。"},
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
        comment="公开文档编号：用于 API、manifest 和审计展示。",
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", name="fk_documents_project_id_projects"),
        nullable=False,
        comment="项目内部主键，引用 projects.id。",
    )
    document_code: Mapped[str | None] = mapped_column(Text, comment="项目内文档业务编号。")
    document_type: Mapped[str] = mapped_column(Text, nullable=False, comment="文档类型。")
    source_type: Mapped[str | None] = mapped_column(Text, comment="来源类型。")
    authorization_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("assets.id", name="fk_documents_authorization_id_assets"),
        comment="授权文件资产，引用 assets.id。",
    )
    domain_metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="场景扩展元数据：K12 学科、年级、考试类型等放这里，不写死在核心字段。",
    )
    split: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'train'"),
        comment="数据集划分：train / val / eval / external_auxiliary。",
    )
    lock_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'unlocked'"),
        comment="锁定状态。",
    )
