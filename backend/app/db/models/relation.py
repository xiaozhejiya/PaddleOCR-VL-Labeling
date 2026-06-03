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
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class RelationObject(TimestampMixin, Base):
    __tablename__ = "relation_objects"
    __table_args__ = (
        UniqueConstraint("revision_id", "rel_id", name="uq_relation_objects_revision_rel"),
        ForeignKeyConstraint(
            ["revision_id", "from_ann_id"],
            ["annotation_objects.revision_id", "annotation_objects.ann_id"],
            name="fk_relation_objects_from_annotation_object",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        ForeignKeyConstraint(
            ["revision_id", "to_ann_id"],
            ["annotation_objects.revision_id", "annotation_objects.ann_id"],
            name="fk_relation_objects_to_annotation_object",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint(
            "status IN ('active', 'deleted')",
            name="ck_relation_objects_status",
        ),
        CheckConstraint(
            "btrim(rel_id) <> ''",
            name="ck_relation_objects_rel_id_not_blank",
        ),
        CheckConstraint(
            "btrim(relation_type) <> ''",
            name="ck_relation_objects_relation_type_not_blank",
        ),
        CheckConstraint(
            "btrim(from_ann_id) <> ''",
            name="ck_relation_objects_from_ann_id_not_blank",
        ),
        CheckConstraint(
            "btrim(to_ann_id) <> ''",
            name="ck_relation_objects_to_ann_id_not_blank",
        ),
        CheckConstraint(
            "from_ann_id <> to_ann_id",
            name="ck_relation_objects_distinct_ann",
        ),
        CheckConstraint(
            "jsonb_typeof(attributes_json) = 'object'",
            name="ck_relation_objects_attributes_json_object",
        ),
        Index("ix_relation_objects_revision_id", "revision_id"),
        Index("ix_relation_objects_relation_type", "relation_type"),
        {"comment": "关系对象索引表：从 annotation revision JSON 抽取的对象关系索引。"},
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
            name="fk_relation_objects_revision_id_annotation_revisions",
            ondelete="CASCADE",
        ),
        nullable=False,
        comment="标注版本内部主键，引用 annotation_revisions.id。",
    )
    rel_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="关系编号：来自 revision JSON，同一 revision 内唯一。",
    )
    relation_type: Mapped[str] = mapped_column(Text, nullable=False, comment="关系类型。")
    from_ann_id: Mapped[str] = mapped_column(Text, nullable=False, comment="关系起点对象编号。")
    to_ann_id: Mapped[str] = mapped_column(Text, nullable=False, comment="关系终点对象编号。")
    attributes_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="关系属性 JSON。",
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'active'"),
        comment="关系状态。",
    )
