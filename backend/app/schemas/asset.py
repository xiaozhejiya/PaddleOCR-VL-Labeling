from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AssetUploadData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str = Field(
        ...,
        title="资产编号",
        description="平台生成的公开资产编号，用于追踪 raw 文件资产。",
    )
    document_id: str = Field(
        ...,
        title="文档编号",
        description="平台生成的公开文档编号，用于后续页面和标注关联。",
    )
    page_id: str = Field(
        ...,
        title="页面编号",
        description="平台生成的公开页面编号，后续 API path 中的 page_id 指该值。",
    )
    sha256: str = Field(
        ...,
        title="SHA-256",
        description="上传文件内容的 SHA-256，用于完整性校验和防止原始文件覆盖。",
    )
    size_bytes: int = Field(
        ..., title="文件大小", description="上传文件大小，单位 byte。"
    )
    mime_type: str = Field(
        ..., title="MIME 类型", description="后端校验后的图片 MIME 类型。"
    )
    width: int = Field(..., title="页面宽度", description="图片宽度，单位像素。")
    height: int = Field(..., title="页面高度", description="图片高度，单位像素。")
    asset_reused: bool = Field(
        ...,
        title="是否复用资产",
        description="当相同 sha256 的 raw asset 已存在时为 true，此时不会覆盖原始文件。",
    )


class AssetUploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: AssetUploadData = Field(
        ..., title="上传结果", description="资产、文档和页面编号。"
    )
    request_id: str = Field(..., title="请求编号", description="本次请求的追踪编号。")
