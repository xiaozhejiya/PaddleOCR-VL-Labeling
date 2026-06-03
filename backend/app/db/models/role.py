from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
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


class RoleRegistry(TimestampMixin, Base):
    __tablename__ = "role_registry"
    __table_args__ = (
        UniqueConstraint("code", name="uq_role_registry_code"),
        UniqueConstraint("id", "scope", name="uq_role_registry_id_scope"),
        CheckConstraint(
            "scope IN ('system', 'project')",
            name="ck_role_registry_scope",
        ),
        CheckConstraint("btrim(code) <> ''", name="ck_role_registry_code_not_blank"),
        CheckConstraint(
            "btrim(display_name) <> ''",
            name="ck_role_registry_display_name_not_blank",
        ),
        CheckConstraint(
            "jsonb_typeof(permissions_json) = 'object'",
            name="ck_role_registry_permissions_json_object",
        ),
        {"comment": "角色注册表：保存系统内置角色和权限 JSON，是 capability 计算来源之一。"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
        comment="内部主键。",
    )
    code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="角色编码：viewer / annotator / reviewer / data_manager / exporter / project_admin / system_admin。",
    )
    display_name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="角色显示名称。",
    )
    scope: Mapped[str] = mapped_column(Text, nullable=False, comment="角色作用域：system / project。")
    description: Mapped[str | None] = mapped_column(Text, comment="角色说明。")
    permissions_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="权限 JSON：后端 capability 计算使用，前端只消费计算结果。",
    )
    is_builtin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        comment="是否内置角色。",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        comment="是否启用。",
    )


class ProjectMember(TimestampMixin, Base):
    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "user_id",
            name="uq_project_members_project_user",
        ),
        CheckConstraint(
            "member_status IN ('active', 'disabled', 'invited', 'removed')",
            name="ck_project_members_status",
        ),
        Index("ix_project_members_project_id", "project_id"),
        Index("ix_project_members_user_id", "user_id"),
        {"comment": "项目成员表：保存用户和项目的成员关系。"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
        comment="内部主键。",
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", name="fk_project_members_project_id_projects"),
        nullable=False,
        comment="项目内部主键，引用 projects.id。",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_project_members_user_id_users"),
        nullable=False,
        comment="用户内部主键，引用 users.id。",
    )
    member_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'active'"),
        comment="成员状态：active / disabled / invited / removed。",
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        comment="加入时间。",
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_project_members_created_by_users"),
        comment="创建人：引用 users.id，保留成员加入来源。",
    )
    removed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        comment="移除时间。",
    )


class MemberRoleBinding(TimestampMixin, Base):
    __tablename__ = "member_role_bindings"
    __table_args__ = (
        ForeignKeyConstraint(
            ["role_id", "role_scope"],
            ["role_registry.id", "role_registry.scope"],
            name="fk_member_role_bindings_role_registry_project",
        ),
        CheckConstraint(
            "status IN ('active', 'revoked')",
            name="ck_member_role_bindings_status",
        ),
        CheckConstraint(
            "role_scope = 'project'",
            name="ck_member_role_bindings_role_scope_project",
        ),
        Index(
            "uq_member_role_bindings_active_member_role",
            "project_member_id",
            "role_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
        Index("ix_member_role_bindings_role_id", "role_id"),
        {"comment": "成员角色绑定表：保存项目成员与项目级角色的授权和撤销记录。"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
        comment="内部主键。",
    )
    project_member_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "project_members.id",
            name="fk_member_role_bindings_project_member_id_project_members",
        ),
        nullable=False,
        comment="项目成员内部主键，引用 project_members.id。",
    )
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="角色内部主键。")
    role_scope: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'project'"),
        comment="角色作用域冗余列：固定为 project，用于数据库层禁止绑定系统级角色。",
    )
    granted_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_member_role_bindings_granted_by_users"),
        comment="授权人，引用 users.id。",
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        comment="授权时间。",
    )
    revoked_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_member_role_bindings_revoked_by_users"),
        comment="撤销人，引用 users.id。",
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        comment="撤销时间。",
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'active'"),
        comment="绑定状态：active 表示当前有效，revoked 表示已撤销。",
    )
