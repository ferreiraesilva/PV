from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(validate_by_name=True)


class TokenPair(BaseModel):
    accessToken: str = Field(..., alias="access_token")
    refreshToken: str = Field(..., alias="refresh_token")
    expiresIn: int = Field(..., alias="expires_in")

    model_config = ConfigDict(populate_by_name=True)


class RefreshRequest(BaseModel):
    refreshToken: str

    model_config = ConfigDict(validate_by_name=True)


class TokenRefresh(BaseModel):
    accessToken: str = Field(..., alias="access_token")
    expiresIn: int = Field(..., alias="expires_in")

    model_config = ConfigDict(populate_by_name=True)


class LogoutRequest(BaseModel):
    refreshToken: str

    model_config = ConfigDict(validate_by_name=True)


class AuditLogEntry(BaseModel):
    id: int
    occurredAt: datetime
    requestId: str
    tenantId: str
    userId: str | None
    method: str
    endpoint: str
    statusCode: int

    model_config = ConfigDict(validate_by_name=True)
