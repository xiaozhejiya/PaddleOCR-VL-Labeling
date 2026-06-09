from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    page_id: str
    project_id: int
    filename: str
    status: str
    width: int
    height: int
    created_at: datetime
    updated_at: datetime


class PageListOut(BaseModel):
    items: list[PageOut]
    total: int
