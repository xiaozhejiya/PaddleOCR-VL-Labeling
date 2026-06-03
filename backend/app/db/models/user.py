from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Identity,
    Index,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        CheckConstraint("btrim(username) <> ''", name="ck_users_username_not_blank"),
        CheckConstraint(
            "btrim(display_name) <> ''",
            name="ck_users_display_name_not_blank",
        ),
        CheckConstraint(
            "status IN ('active', 'disabled', 'pending')",
            name="ck_users_status",
        ),
        Index(
            "uq_users_email",
            "email",
            unique=True,
            postgresql_where=text("email IS NOT NULL"),
        ),
        {"comment": "用户表：保存平台账号，是审计、创建人、复核人和权限校验的基础事实来源。"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
        comment="内部主键。",
    )
    username: Mapped[str] = mapped_column(Text, nullable=False, comment="登录用户名。")
    email: Mapped[str | None] = mapped_column(Text, comment="邮箱。")
    display_name: Mapped[str] = mapped_column(Text, nullable=False, comment="显示名称。")
    password_hash: Mapped[str | None] = mapped_column(
        Text,
        comment="密码哈希：不得明文保存，不得返回前端。",
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'pending'"),
        comment="用户状态：active 可用，disabled 禁用，pending 待初始化。",
    )
    is_system_admin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
        comment="系统管理员标记：只用于系统级初始化和维护，不替代项目角色。",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        comment="最近登录时间。",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        comment="软删除时间。",
    )
