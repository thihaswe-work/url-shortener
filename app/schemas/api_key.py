from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ApiKeyCreate(BaseModel):
    name: str


class ApiKeyResponse(BaseModel):
    id: int
    key_prefix: str
    name: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ApiKeyCreated(ApiKeyResponse):
    raw_key: str


class ApiKeyList(BaseModel):
    api_keys: list[ApiKeyResponse]
