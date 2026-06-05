from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ShortenRequest(BaseModel):
    original_url: str = Field(..., description="The URL to shorten")
    custom_alias: Optional[str] = Field(
        None, min_length=4, max_length=32, description="Custom short code"
    )
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")


class URLResponse(BaseModel):
    short_code: str
    original_url: str
    short_url: str
    custom_alias: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    click_count: int = 0

    model_config = {"from_attributes": True}
