from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AnnotationRevisionReadData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_id: str = Field(
        ..., title="标注版本编号", description="标注 revision 公开编号。"
    )
    page_id: str = Field(..., title="页面编号", description="页面公开稳定编号。")
    revision_no: int = Field(
        ..., title="版本号", description="同一页面内递增的版本号。"
    )
    status: str = Field(
        ..., title="版本状态", description="draft / submitted / reviewed / locked。"
    )
    qc_status: str = Field(
        ..., title="质检状态", description="pending / passed / failed / warning。"
    )
    sha256: str | None = Field(
        None, title="JSON SHA-256", description="revision JSON 文件 SHA-256。"
    )
    size_bytes: int | None = Field(
        None, title="JSON 大小", description="revision JSON 文件大小。"
    )
    annotation_json: dict[str, Any] = Field(
        ...,
        title="标注 JSON",
        description="整页标注主 JSON，包含 k12_annotations、relations、history 等字段。",
    )


class AnnotationRevisionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: AnnotationRevisionReadData | None = Field(
        ..., title="标注版本", description="页面尚无标注版本时返回 null。"
    )
    request_id: str = Field(..., title="请求编号", description="本次请求的追踪编号。")


class AnnotationRevisionListItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_id: str = Field(..., title="标注版本编号", description="标注 revision 公开编号。")
    page_id: str = Field(..., title="页面编号", description="页面公开稳定编号。")
    revision_no: int = Field(..., title="版本号", description="同一页面内递增的版本号。")
    status: str = Field(..., title="版本状态", description="draft / submitted / reviewed / locked。")
    qc_status: str = Field(..., title="质检状态", description="pending / passed / failed / warning。")
    created_at: datetime | None = Field(None, title="创建时间", description="版本创建时间。")
    change_summary: str | None = Field(None, title="变更摘要", description="版本变更摘要。")


class AnnotationRevisionListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AnnotationRevisionListItem]
    total: int
