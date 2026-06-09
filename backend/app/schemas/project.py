from __future__ import annotations

from datetime import datetime

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
