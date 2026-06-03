from __future__ import annotations


from sqlalchemy import (
    BigInteger,
    CheckConstraint,
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


class Page(TimestampMixin, Base):
    __tablename__ = "pages"
    __table_args__ = (
        UniqueConstraint("public_id", name="uq_pages_public_id"),
        UniqueConstraint("id", "document_id", name="uq_pages_id_document"),
        UniqueConstraint("document_id", "page_index", name="uq_pages_document_page_index"),
        CheckConstraint("page_index >= 0", name="ck_pages_page_index"),
        CheckConstraint("width > 0", name="ck_pages_width"),
        CheckConstraint("height > 0", name="ck_pages_height"),
        CheckConstraint(
            "status IN ('imported', 'preannotated', 'annotated', 'reviewed', 'locked')",
            name="ck_pages_status",
        ),
        CheckConstraint("btrim(public_id) <> ''", name="ck_pages_public_id_not_blank"),
        Index("ix_pages_document_id", "document_id"),
        Index("ix_pages_status", "status"),
        Index("ix_pages_visual_difficulty", "visual_difficulty"),
        {"comment": "页面表：保存文档页和页面图像的关系。"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
        comment="页面内部主键：仅用于数据库关联。",
    )
    document_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("documents.id", name="fk_pages_document_id_documents"),
        nullable=False,
        comment="文档内部主键：引用 documents.id。",
    )
    public_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="公开稳定页面编号：前端路由、API path 和审计展示使用。",
    )
    page_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="文档内页序号，从 0 开始。",
    )
    image_asset_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("assets.id", name="fk_pages_image_asset_id_assets"),
        comment="页面图像资产，引用 assets.id。",
    )
    width: Mapped[int] = mapped_column(Integer, nullable=False, comment="页面宽度。")
    height: Mapped[int] = mapped_column(Integer, nullable=False, comment="页面高度。")
    capture_method: Mapped[str | None] = mapped_column(Text, comment="采集方式。")
    visual_difficulty: Mapped[str | None] = mapped_column(Text, comment="视觉难度标签。")
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'imported'"),
        comment="页面状态。",
    )
