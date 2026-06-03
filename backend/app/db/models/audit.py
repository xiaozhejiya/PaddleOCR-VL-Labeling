from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint("btrim(action) <> ''", name="ck_audit_logs_action_not_blank"),
        CheckConstraint(
            "btrim(resource_type) <> ''",
            name="ck_audit_logs_resource_type_not_blank",
        ),
        CheckConstraint(
            "before_json IS NULL OR jsonb_typeof(before_json) = 'object'",
            name="ck_audit_logs_before_json_object",
        ),
        CheckConstraint(
            "after_json IS NULL OR jsonb_typeof(after_json) = 'object'",
            name="ck_audit_logs_after_json_object",
        ),
        Index("ix_audit_logs_project_id", "project_id"),
        Index("ix_audit_logs_actor_id", "actor_id"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_created_at", "created_at"),
        {"comment": "审计日志表：保存角色变更、成员管理、锁定、回滚、导出和下载等关键操作。"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
        comment="内部主键。",
    )
    project_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", name="fk_audit_logs_project_id_projects"),
        comment="项目内部主键，引用 projects.id。",
    )
    actor_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_audit_logs_actor_id_users"),
        comment="操作人，引用 users.id。",
    )
    action: Mapped[str] = mapped_column(Text, nullable=False, comment="动作编码。")
    resource_type: Mapped[str] = mapped_column(Text, nullable=False, comment="资源类型。")
    resource_id: Mapped[str | None] = mapped_column(
        Text,
        comment="资源编号：优先记录对外展示的公开编号，内部排查场景可记录带前缀的内部编号。",
    )
    before_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, comment="操作前快照 JSON。")
    after_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, comment="操作后快照 JSON。")
    request_id: Mapped[str | None] = mapped_column(Text, comment="请求 ID。")
    ip_address: Mapped[str | None] = mapped_column(INET, comment="客户端 IP。")
    user_agent: Mapped[str | None] = mapped_column(Text, comment="User-Agent。")
    prev_hash: Mapped[str | None] = mapped_column(
        CHAR(64),
        comment="上一条审计哈希：后续用于审计日志哈希链。",
    )
    entry_hash: Mapped[str | None] = mapped_column(
        CHAR(64),
        comment="当前审计哈希：后续用于审计日志哈希链。",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        comment="创建时间。",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        comment="更新时间。audit_logs 禁止 UPDATE，该字段用于满足 M2 统一字段要求。",
    )
