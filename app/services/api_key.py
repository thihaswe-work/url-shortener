import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.api_key import ApiKey


def _generate_raw_key() -> str:
    return f"shortener_{secrets.token_urlsafe(32)}"


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def _prefix(key: str) -> str:
    return key[:16] + "..."


class ApiKeyService:
    def __init__(self, db: Session):
        self.db = db

    def create_key(self, user_id: int, name: str) -> tuple[ApiKey, str]:
        raw_key = _generate_raw_key()
        key_hash = _hash_key(raw_key)
        api_key = ApiKey(
            user_id=user_id,
            key_hash=key_hash,
            key_prefix=_prefix(raw_key),
            name=name,
        )
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        return api_key, raw_key

    def list_keys(self, user_id: int) -> list[ApiKey]:
        return (
            self.db.query(ApiKey)
            .filter(ApiKey.user_id == user_id)
            .order_by(ApiKey.created_at.desc())
            .all()
        )

    def revoke_key(self, key_id: int, user_id: int) -> None:
        api_key = self.db.query(ApiKey).filter(
            ApiKey.id == key_id,
            ApiKey.user_id == user_id,
        ).first()
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
            )
        api_key.is_active = False
        self.db.commit()

    def validate_key(self, raw_key: str) -> ApiKey:
        key_hash = _hash_key(raw_key)
        api_key = self.db.query(ApiKey).filter(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active == True,
        ).first()
        if api_key:
            api_key.last_used_at = datetime.now(timezone.utc)
            self.db.commit()
        return api_key
