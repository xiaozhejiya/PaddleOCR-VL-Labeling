from __future__ import annotations

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Identity, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class Project(TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("btrim(name) <> ''", name="ck_projects_name_not_blank"),
        CheckConstraint(
            "btrim(schema_version) <> ''",
            name="ck_projects_schema_version_not_blank",
        ),
        {"comment": "项目表：保存标注项目的基础信息和 schema 版本。"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
        comment="内部主键：BIGINT identity，仅用于数据库关联。",
    )
    name: Mapped[str] = mapped_column(Text, nullable=False, comment="项目名称。")
    description: Mapped[str | None] = mapped_column(Text, comment="项目说明。")
    schema_version: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'v1'"),
        comment="项目 schema 版本：用于后续数据格式升级和兼容判断。",
    )
    created_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        comment="创建者用户 ID。",
    )
