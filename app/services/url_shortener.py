import secrets
import string
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.url import URL


def _generate_short_code(length: int = 7) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class URLShortenerService:
    def __init__(self, db: Session):
        self.db = db

    def create_short_url(
        self,
        original_url: str,
        custom_alias: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        user_id: Optional[int] = None,
    ) -> URL:
        if custom_alias:
            existing = self.db.query(URL).filter(
                URL.short_code == custom_alias
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Custom alias already in use",
                )
            short_code = custom_alias
        else:
            for _ in range(10):
                short_code = _generate_short_code()
                if not self.db.query(URL).filter(
                    URL.short_code == short_code
                ).first():
                    break
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate unique short code",
                )

        url = URL(
            short_code=short_code,
            original_url=original_url,
            custom_alias=bool(custom_alias),
            user_id=user_id,
            expires_at=expires_at,
        )
        self.db.add(url)
        self.db.commit()
        self.db.refresh(url)
        return url

    def get_url_by_code(self, short_code: str) -> Optional[URL]:
        return self.db.query(URL).filter(URL.short_code == short_code).first()

    def get_user_urls(self, user_id: int) -> list[URL]:
        return (
            self.db.query(URL)
            .filter(URL.user_id == user_id)
            .order_by(URL.created_at.desc())
            .all()
        )
