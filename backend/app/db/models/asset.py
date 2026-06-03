from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class Asset(TimestampMixin, Base):
    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint("public_id", name="uq_assets_public_id"),
        UniqueConstraint("sha256", name="uq_assets_sha256"),
        CheckConstraint("size_bytes >= 0", name="ck_assets_size_bytes"),
        CheckConstraint("width IS NULL OR width > 0", name="ck_assets_width"),
        CheckConstraint("height IS NULL OR height > 0", name="ck_assets_height"),
        CheckConstraint("btrim(public_id) <> ''", name="ck_assets_public_id_not_blank"),
        CheckConstraint(
            "btrim(asset_type) <> ''",
            name="ck_assets_asset_type_not_blank",
        ),
        CheckConstraint(
            "btrim(storage_path) <> ''",
            name="ck_assets_storage_path_not_blank",
        ),
        Index("ix_assets_asset_type", "asset_type"),
        {"comment": "文件资产表：保存原始文件、页面图像、标注 JSON、导出文件等文件级元数据。"},
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
        comment="公开资产编号：用于 API、manifest 和文件追踪，不作为数据库外键主键。",
    )
    asset_type: Mapped[str] = mapped_column(Text, nullable=False, comment="资产类型。")
    storage_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="受控存储相对路径：不得直接来自前端任意路径。",
    )
    original_filename: Mapped[str | None] = mapped_column(Text, comment="原始文件名。")
    mime_type: Mapped[str | None] = mapped_column(Text, comment="MIME 类型。")
    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="文件大小，单位 byte。",
    )
    sha256: Mapped[str] = mapped_column(
        CHAR(64),
        nullable=False,
        comment="文件 SHA-256：用于完整性校验和防覆盖。",
    )
    width: Mapped[int | None] = mapped_column(Integer, comment="图像宽度。")
    height: Mapped[int | None] = mapped_column(Integer, comment="图像高度。")
    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_assets_created_by_users"),
        comment="创建人，引用 users.id。",
    )
    readonly: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        comment="只读标记：原始资产、模型输出和历史 revision 默认只追加不覆盖。",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        comment="软删除时间。",
    )
