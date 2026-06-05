from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.url_shortener import URLShortenerService
from app.services.analytics import AnalyticsService
from app.core.redis import cache_get, cache_setex

router = APIRouter(tags=["Redirect"])


@router.get("/{short_code}")
def redirect_to_url(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    cache_key = f"url:{short_code}"

    cached = cache_get(cache_key)
    if cached:
        original_url = cached
    else:
        service = URLShortenerService(db)
        url = service.get_url_by_code(short_code)
        if not url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short URL not found",
            )
        if url.expires_at and url.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Short URL has expired",
            )
        original_url = url.original_url
        cache_setex(cache_key, 3600, original_url)

    analytics = AnalyticsService(db)
    analytics.track_click(
        short_code=short_code,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer"),
    )

    return RedirectResponse(url=original_url, status_code=status.HTTP_301_MOVED_PERMANENTLY)
