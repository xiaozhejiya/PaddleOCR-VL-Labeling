from __future__ import annotations

from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
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


class LabelRegistry(TimestampMixin, Base):
    __tablename__ = "label_registry"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_label_registry_project_id_projects",
        ),
        CheckConstraint(
            "btrim(namespace) <> ''",
            name="ck_label_registry_namespace_not_blank",
        ),
        CheckConstraint("btrim(name) <> ''", name="ck_label_registry_name_not_blank"),
        CheckConstraint(
            "btrim(display_name) <> ''",
            name="ck_label_registry_display_name_not_blank",
        ),
        CheckConstraint(
            "jsonb_typeof(geometry_types_json) = 'array'",
            name="ck_label_registry_geometry_types_json_array",
        ),
        CheckConstraint(
            "jsonb_typeof(attributes_schema_json) = 'object'",
            name="ck_label_registry_attributes_schema_json_object",
        ),
        UniqueConstraint(
            "project_id",
            "namespace",
            "name",
            name="uq_label_registry_project_namespace_name",
            postgresql_nulls_not_distinct=True,
        ),
        Index("ix_label_registry_project_id", "project_id"),
        Index("ix_label_registry_namespace_name", "namespace", "name"),
        {"comment": "标签注册表：保存官方 layout 标签和场景扩展标签。"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
        comment="内部主键。",
    )
    project_id: Mapped[int | None] = mapped_column(BigInteger, comment="所属项目：为空表示全局内置标签。")
    namespace: Mapped[str] = mapped_column(Text, nullable=False, comment="标签命名空间。")
    name: Mapped[str] = mapped_column(Text, nullable=False, comment="标签名称。")
    display_name: Mapped[str] = mapped_column(Text, nullable=False, comment="标签显示名称。")
    geometry_types_json: Mapped[list[Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
        comment="允许的几何类型列表，例如 bbox_xyxy / quad / polygon。",
    )
    attributes_schema_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="标签属性 schema：用于后续 schema QC。",
    )
    exportable_to_pp_doclayout_v3: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
        comment="是否可导出为 PP-DocLayoutV3 标签。",
    )
    default_color: Mapped[str | None] = mapped_column(Text, comment="默认显示颜色。")
    is_builtin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
        comment="是否内置标签。",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        comment="是否启用。",
    )
