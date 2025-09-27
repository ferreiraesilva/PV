from sqlalchemy.orm import Session

from app.db.models import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, tenant_id: str, email: str) -> User | None:
        return (
            self.session.query(User)
            .filter(User.tenant_id == tenant_id, User.email == email)
            .one_or_none()
        )

    def create(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
