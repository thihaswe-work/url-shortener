import hashlib
from typing import Optional

from sqlalchemy.orm import Session

from app.models.click import Click
from app.models.url import URL


def _hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def _detect_device(user_agent: Optional[str]) -> str:
    if not user_agent:
        return "unknown"
    ua = user_agent.lower()
    if "mobile" in ua or "android" in ua or "iphone" in ua or "blackberry" in ua:
        return "mobile"
    if "tablet" in ua or "ipad" in ua or "playbook" in ua:
        return "tablet"
    return "desktop"


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def track_click(
        self,
        short_code: str,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
    ) -> None:
        url = self.db.query(URL).filter(URL.short_code == short_code).first()
        if not url:
            return

        click = Click(
            url_id=url.id,
            ip_hash=_hash_ip(ip) if ip else None,
            user_agent=user_agent,
            referrer=referrer,
            device_type=_detect_device(user_agent),
        )
        url.click_count = (url.click_count or 0) + 1
        self.db.add(click)
        self.db.commit()

    def get_stats(self, short_code: str) -> Optional[dict]:
        url = self.db.query(URL).filter(URL.short_code == short_code).first()
        if not url:
            return None

        clicks = (
            self.db.query(Click)
            .filter(Click.url_id == url.id)
            .order_by(Click.timestamp.desc())
            .limit(100)
            .all()
        )
        return {
            "short_code": short_code,
            "original_url": url.original_url,
            "total_clicks": url.click_count or 0,
            "recent_clicks": clicks,
        }
