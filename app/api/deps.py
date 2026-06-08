from fastapi import Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.core.security import decode_token
from app.services.api_key import ApiKeyService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


def _get_user_by_jwt(token: str, db: Session) -> User:
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def _get_user_by_api_key(api_key: str, db: Session) -> User:
    service = ApiKeyService(db)
    key = service.validate_key(api_key)
    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
        )
    user = db.query(User).filter(User.id == key.user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    x_api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> User:
    if token:
        return _get_user_by_jwt(token, db)
    if x_api_key:
        return _get_user_by_api_key(x_api_key, db)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide JWT token or API key.",
    )


def get_optional_user(
    token: str = Depends(oauth2_scheme),
    x_api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> User:
    if token:
        try:
            return _get_user_by_jwt(token, db)
        except HTTPException:
            return None
    if x_api_key:
        try:
            return _get_user_by_api_key(x_api_key, db)
        except HTTPException:
            return None
    return None
