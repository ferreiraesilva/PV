from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    fullName: Optional[str] = None
    roles: List[str] = []
    isActive: bool = True
    isSuperuser: bool = False

    model_config = ConfigDict(validate_by_name=True)


class User(UserBase):
    id: str
    tenantId: str
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(validate_by_name=True)


class UserCreate(UserBase):
    password: str

    model_config = ConfigDict(validate_by_name=True)


class UserPatch(BaseModel):
    fullName: Optional[str] = None
    password: Optional[str] = None
    isActive: Optional[bool] = None
    roles: Optional[List[str]] = None

    model_config = ConfigDict(validate_by_name=True)
