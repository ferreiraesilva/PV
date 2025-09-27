from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, TokenPair, TokenRefresh
from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.db.repositories.user import UserRepository
from app.db.session import get_db

router = APIRouter(tags=["Auth"])
settings = get_settings()


@router.post("/login", response_model=TokenPair)
def login(tenant_id: str, payload: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    repository = UserRepository(db)
    user = repository.get_by_email(tenant_id, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    roles: list[str] = ["superuser"] if user.is_superuser else ["user"]
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"tenant_id": str(user.tenant_id), "roles": roles},
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenRefresh)
def refresh(tenant_id: str, payload: RefreshRequest) -> TokenRefresh:
    # Token validation will be implemented in later stages.
    new_access_token = create_access_token(
        subject="refresh-placeholder",
        extra_claims={"tenant_id": tenant_id},
    )
    return TokenRefresh(access_token=new_access_token, expires_in=settings.access_token_expire_minutes * 60)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(tenant_id: str, payload: LogoutRequest) -> None:
    # Token revocation will be implemented in later stages.
    return None
