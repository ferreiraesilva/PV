from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    def get_by_email(self, tenant_id: UUID | str, email: str) -> User | None:
        normalized = self._normalize_email(email)
        stmt = select(User).where(User.tenant_id == tenant_id, User.email == normalized)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_id(self, user_id: UUID | str) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_email_unscoped(self, email: str) -> list[User]:
        normalized = self._normalize_email(email)
        stmt = select(User).where(User.email == normalized)
        return self.session.execute(stmt).scalars().all()

    def count_active_by_tenant(self, tenant_id: UUID | str) -> int:
        stmt = (
            select(func.count())
            .select_from(User)
            .where(User.tenant_id == tenant_id, User.is_active.is_(True))
        )
        return int(self.session.execute(stmt).scalar_one())

    def create(self, user: User) -> User:
        user.email = self._normalize_email(user.email)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def save(self, user: User) -> User:
        user.email = self._normalize_email(user.email)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
