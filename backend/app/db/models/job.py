from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class BackgroundJob(TimestampMixin, Base):
    __tablename__ = "background_jobs"
    __table_args__ = (
        UniqueConstraint("public_id", name="uq_background_jobs_public_id"),
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'canceled')",
            name="ck_background_jobs_status",
        ),
        CheckConstraint(
            "progress >= 0 AND progress <= 100",
            name="ck_background_jobs_progress",
        ),
        CheckConstraint(
            "btrim(public_id) <> ''",
            name="ck_background_jobs_public_id_not_blank",
        ),
        CheckConstraint(
            "btrim(job_type) <> ''",
            name="ck_background_jobs_job_type_not_blank",
        ),
        CheckConstraint(
            "jsonb_typeof(payload_json) = 'object'",
            name="ck_background_jobs_payload_json_object",
        ),
        CheckConstraint(
            "jsonb_typeof(result_json) = 'object'",
            name="ck_background_jobs_result_json_object",
        ),
        Index("ix_background_jobs_job_type", "job_type"),
        Index("ix_background_jobs_status", "status"),
        {"comment": "后台任务表：保存长任务状态和结果摘要；Redis 只作为队列，不保存业务事实。"},
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
        comment="公开任务编号：用于 API 查询和任务 artifact 路径。",
    )
    job_type: Mapped[str] = mapped_column(Text, nullable=False, comment="任务类型。")
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'queued'"),
        comment="任务状态。",
    )
    payload_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="任务载荷 JSON。",
    )
    result_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="任务结果 JSON。",
    )
    progress: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        server_default=text("0"),
        comment="任务进度：0 到 100。",
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_background_jobs_created_by_users"),
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
