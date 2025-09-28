from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        token_id: UUID,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        user_agent: Optional[str],
        ip_address: Optional[str],
    ) -> RefreshToken:
        token = RefreshToken(
            id=token_id,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.session.add(token)
        self.session.commit()
        self.session.refresh(token)
        return token

    def get_active(self, token_id: UUID, reference: datetime) -> RefreshToken | None:
        return (
            self.session.query(RefreshToken)
            .filter(
                RefreshToken.id == token_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > reference,
            )
            .one_or_none()
        )

    def revoke(self, token: RefreshToken) -> RefreshToken:
        token.revoked_at = datetime.now(timezone.utc)
        self.session.add(token)
        self.session.commit()
        self.session.refresh(token)
        return token

    def revoke_all_for_user(self, user_id: UUID) -> None:
        (
            self.session.query(RefreshToken)
            .filter(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .update({"revoked_at": datetime.now(timezone.utc)}, synchronize_session=False)
        )
        self.session.commit()
