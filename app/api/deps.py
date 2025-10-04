from typing import Annotated, Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import pwd_context
from app.db.session import get_db

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/t/{tenant_id}/login")


class CurrentUser:
    def __init__(self, user_id: str, tenant_id: str, roles: list[str]):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.roles = roles


async def get_current_user(request: Request, token: Annotated[str, Depends(oauth2_scheme)]) -> CurrentUser:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:  # pragma: no cover - defensive guard
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from exc

    user_id: str | None = payload.get("sub")
    tenant_id: str | None = payload.get("tenant_id")
    roles: list[str] = payload.get("roles", [])
    if not user_id or not tenant_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    current_user = CurrentUser(user_id=user_id, tenant_id=tenant_id, roles=roles)
    request.state.current_user = current_user
    request.state.tenant_id = tenant_id
    return current_user


def require_roles(*expected_roles: str) -> Callable[[CurrentUser], CurrentUser]:
    def _checker(current_user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if not set(expected_roles).intersection(current_user.roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return _checker


SessionDependency = Annotated[Session, Depends(get_db)]
PasswordHasher = pwd_context
