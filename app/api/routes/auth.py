from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, TokenPair, TokenRefresh
from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.repositories.refresh_token import RefreshTokenRepository
from app.db.repositories.user import UserRepository
from app.db.session import get_db

router = APIRouter(tags=["Auth"])
settings = get_settings()


def _issue_refresh_token(
    repository: RefreshTokenRepository,
    *,
    user_id: UUID,
    user_agent: str | None,
    ip_address: str | None,
) -> str:
    token_id = uuid4()
    secret = uuid4().hex
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.refresh_token_expire_minutes)
    repository.create(
        token_id=token_id,
        user_id=user_id,
        token_hash=get_password_hash(secret),
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    return f"{token_id}:{secret}"


def _split_refresh_token(raw_token: str) -> tuple[UUID, str]:
    try:
        token_id_str, secret = raw_token.split(":", 1)
        return UUID(token_id_str), secret
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token format") from None


@router.post("/login", response_model=TokenPair)
def login(
    tenant_id: str,
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenPair:
    repository = UserRepository(db)
    user = repository.get_by_email(tenant_id, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    roles: list[str] = ["superuser"] if user.is_superuser else ["user"]
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"tenant_id": str(user.tenant_id), "roles": roles},
    )

    refresh_repo = RefreshTokenRepository(db)
    refresh_token = _issue_refresh_token(
        refresh_repo,
        user_id=user.id,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenRefresh)
def refresh(
    tenant_id: str,
    payload: RefreshRequest,
    db: Session = Depends(get_db),
) -> TokenRefresh:
    token_id, secret = _split_refresh_token(payload.refreshToken)

    refresh_repo = RefreshTokenRepository(db)
    stored_token = refresh_repo.get_active(token_id, datetime.now(timezone.utc))
    if not stored_token or not verify_password(secret, stored_token.token_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(stored_token.user_id)
    if not user or str(user.tenant_id) != tenant_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    roles: list[str] = ["superuser"] if user.is_superuser else ["user"]
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"tenant_id": str(user.tenant_id), "roles": roles},
    )

    return TokenRefresh(access_token=access_token, expires_in=settings.access_token_expire_minutes * 60)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    tenant_id: str,
    payload: LogoutRequest,
    db: Session = Depends(get_db),
) -> None:
    token_id, secret = _split_refresh_token(payload.refreshToken)

    refresh_repo = RefreshTokenRepository(db)
    stored_token = refresh_repo.get_active(token_id, datetime.now(timezone.utc))
    if not stored_token or not verify_password(secret, stored_token.token_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token")

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(stored_token.user_id)
    if not user or str(user.tenant_id) != tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token")

    refresh_repo.revoke(stored_token)
    return None
