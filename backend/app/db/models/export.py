from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
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


class ExportJob(TimestampMixin, Base):
    __tablename__ = "export_jobs"
    __table_args__ = (
        UniqueConstraint("public_id", name="uq_export_jobs_public_id"),
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'canceled')",
            name="ck_export_jobs_status",
        ),
        CheckConstraint(
            "btrim(public_id) <> ''",
            name="ck_export_jobs_public_id_not_blank",
        ),
        CheckConstraint(
            "btrim(export_type) <> ''",
            name="ck_export_jobs_export_type_not_blank",
        ),
        CheckConstraint(
            "jsonb_typeof(export_profile_json) = 'object'",
            name="ck_export_jobs_export_profile_json_object",
        ),
        CheckConstraint(
            "jsonb_typeof(input_scope_json) = 'object'",
            name="ck_export_jobs_input_scope_json_object",
        ),
        CheckConstraint(
            "jsonb_typeof(source_revisions_json) = 'array'",
            name="ck_export_jobs_source_revisions_json_array",
        ),
        Index("ix_export_jobs_project_id", "project_id"),
        Index("ix_export_jobs_status", "status"),
        {"comment": "导出任务表：保存导出请求、状态、范围、输出路径和报告资产。"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
        comment="内部主键。",
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", name="fk_export_jobs_project_id_projects"),
        nullable=False,
        comment="项目内部主键，引用 projects.id。",
    )
    public_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="公开导出编号：用于 API、manifest 和 artifact 路径。",
    )
    export_type: Mapped[str] = mapped_column(Text, nullable=False, comment="导出类型。")
    export_profile_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="导出配置 JSON。",
    )
    input_scope_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="导出输入范围 JSON。",
    )
    source_revisions_json: Mapped[list[Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
        comment="来源 revision 列表：用于导出包可追溯。",
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'queued'"),
        comment="导出状态。",
    )
    output_dir: Mapped[str | None] = mapped_column(Text, comment="导出输出目录。")
    report_asset_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("assets.id", name="fk_export_jobs_report_asset_id_assets"),
        comment="导出报告资产，引用 assets.id。",
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_export_jobs_created_by_users"),
        comment="创建人，引用 users.id。",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        comment="开始时间。",
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        comment="结束时间。",
    )
    error_message: Mapped[str | None] = mapped_column(Text, comment="错误信息。")
