from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ClickResponse(BaseModel):
    timestamp: datetime
    ip_hash: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    device_type: Optional[str] = None

    model_config = {"from_attributes": True}


class StatsResponse(BaseModel):
    short_code: str
    original_url: str
    total_clicks: int
    recent_clicks: list[ClickResponse]
