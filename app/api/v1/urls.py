from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.url import ShortenRequest, URLResponse
from app.schemas.analytics import StatsResponse
from app.services.url_shortener import URLShortenerService
from app.services.analytics import AnalyticsService
from app.api.deps import get_optional_user, get_current_user
from app.models.user import User
from app.utils.rate_limiter import rate_limit_shorten

router = APIRouter(tags=["URLs"])


@router.post(
    "/shorten",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_shorten)],
)
def shorten_url(
    request: Request,
    body: ShortenRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    service = URLShortenerService(db)
    url = service.create_short_url(
        original_url=body.original_url,
        custom_alias=body.custom_alias,
        expires_at=body.expires_at,
        user_id=current_user.id if current_user else None,
    )
    base_url = str(request.base_url).rstrip("/")
    return URLResponse(
        short_code=url.short_code,
        original_url=url.original_url,
        short_url=f"{base_url}/{url.short_code}",
        custom_alias=url.custom_alias,
        expires_at=url.expires_at,
        created_at=url.created_at,
        click_count=url.click_count or 0,
    )


@router.get("/stats/{short_code}", response_model=StatsResponse)
def get_stats(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    url_service = URLShortenerService(db)
    url = url_service.get_url_by_code(short_code)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found",
        )
    if url.user_id and url.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this URL's stats",
        )

    analytics_service = AnalyticsService(db)
    stats = analytics_service.get_stats(short_code)
    return stats
