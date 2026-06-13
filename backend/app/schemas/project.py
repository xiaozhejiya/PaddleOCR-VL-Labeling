from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200, title="项目名称")
    description: str | None = Field(default=None, title="项目说明")


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200, title="项目名称")
    description: str | None = Field(default=None, title="项目说明")


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    schema_version: str
    created_by: int
    created_at: datetime
    updated_at: datetime


class ProjectListOut(BaseModel):
    items: list[ProjectOut]
    total: int


class ProjectLabelOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = Field(default=None, title="标签主键")
    project_id: int | None = Field(default=None, title="所属项目ID")
    namespace: str = Field(..., title="标签命名空间")
    name: str = Field(..., title="标签名称")
    display_name: str = Field(..., title="标签显示名称")
    display_name_i18n: dict[str, str] | None = Field(default=None, title="标签多语言显示名称")
    geometry_types: list[str] = Field(default_factory=list, title="允许的几何类型")
    attributes_schema: dict[str, Any] = Field(default_factory=dict, title="属性Schema")
    default_color: str | None = Field(default=None, title="默认颜色")
    is_builtin: bool = Field(..., title="是否内置标签")
    is_active: bool = Field(..., title="是否启用")


class ProjectLabelListOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ProjectLabelOut] = Field(default_factory=list, title="标签列表")
    total: int = Field(..., title="总数")
