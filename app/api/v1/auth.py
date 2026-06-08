from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreated, ApiKeyList, ApiKeyResponse
from app.services.auth import AuthService
from app.services.api_key import ApiKeyService
from app.api.deps import get_current_user
from app.models.user import User
from app.utils.rate_limiter import rate_limit_auth

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_auth)],
)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.register(request.email, request.username, request.password)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit_auth)],
)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    token = service.login(request.username, request.password)
    return TokenResponse(access_token=token)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/api-keys", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
def create_api_key(
    body: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ApiKeyService(db)
    api_key, raw_key = service.create_key(current_user.id, body.name)
    return ApiKeyCreated(
        id=api_key.id,
        key_prefix=api_key.key_prefix,
        name=api_key.name,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        raw_key=raw_key,
    )


@router.get("/api-keys", response_model=ApiKeyList)
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ApiKeyService(db)
    keys = service.list_keys(current_user.id)
    return ApiKeyList(api_keys=keys)


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ApiKeyService(db)
    service.revoke_key(key_id, current_user.id)
