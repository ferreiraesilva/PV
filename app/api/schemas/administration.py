from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.api.schemas.user import User as UserResponse
from app.api.schemas.user import UserCreate, UserPatch


class TenantCompanyCreate(BaseModel):
    legalName: str
    tradeName: Optional[str] = None
    taxId: str
    billingEmail: EmailStr
    billingPhone: Optional[str] = None
    addressLine1: str
    addressLine2: Optional[str] = None
    city: str
    state: str
    zipCode: str
    country: str = "BR"

    model_config = ConfigDict(populate_by_name=True)


class TenantCompanyResponse(BaseModel):
    id: UUID
    tenantId: UUID
    legalName: str
    tradeName: Optional[str] = None
    taxId: str
    billingEmail: EmailStr
    billingPhone: Optional[str] = None
    addressLine1: str
    addressLine2: Optional[str] = None
    city: str
    state: str
    zipCode: str
    country: str
    isActive: bool
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(populate_by_name=True)


class TenantCompaniesAttachRequest(BaseModel):
    companies: List[TenantCompanyCreate]

    model_config = ConfigDict(populate_by_name=True)


class CompanyUpdateRequest(BaseModel):
    legalName: Optional[str] = None
    tradeName: Optional[str] = None
    taxId: Optional[str] = None
    billingEmail: Optional[EmailStr] = None
    billingPhone: Optional[str] = None
    addressLine1: Optional[str] = None
    addressLine2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipCode: Optional[str] = None
    country: Optional[str] = None
    isActive: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class TenantCreateRequest(BaseModel):
    name: str
    slug: str
    companies: List[TenantCompanyCreate]
    administrators: List[UserCreate]
    metadata: Optional[dict[str, Any]] = None
    planId: Optional[UUID] = None
    isDefault: bool = False

    model_config = ConfigDict(populate_by_name=True)


class PlanCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    maxUsers: Optional[int] = None
    priceCents: Optional[int] = None
    currency: str = "BRL"
    billingCycleMonths: int = 1

    model_config = ConfigDict(populate_by_name=True)


class PlanUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    maxUsers: Optional[int] = None
    priceCents: Optional[int] = None
    currency: Optional[str] = None
    billingCycleMonths: Optional[int] = None
    isActive: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class PlanAssignRequest(BaseModel):
    planId: UUID


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    isActive: bool
    isDefault: bool
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(populate_by_name=True)


class CommercialPlanResponse(BaseModel):
    id: UUID
    tenantId: UUID
    name: str
    description: Optional[str] = None
    maxUsers: Optional[int] = None
    priceCents: Optional[int] = None
    currency: str
    isActive: bool
    billingCycleMonths: int
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(populate_by_name=True)


class TenantPlanSubscriptionResponse(BaseModel):
    id: UUID
    tenantId: UUID
    planId: UUID
    isActive: bool
    activatedAt: datetime
    deactivatedAt: Optional[datetime] = None
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(populate_by_name=True)


class PasswordResetResponse(BaseModel):
    token: str
    expiresAt: datetime

    model_config = ConfigDict(populate_by_name=True)


class PasswordResetConfirmRequest(BaseModel):
    token: str
    newPassword: str

    model_config = ConfigDict(populate_by_name=True)


class UserSuspendRequest(BaseModel):
    reason: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class UserReinstateRequest(BaseModel):
    reactivate: bool = False

    model_config = ConfigDict(populate_by_name=True)


class PaymentPlanInstallmentItem(BaseModel):
    period: int = Field(..., ge=1)
    amount: float = Field(..., gt=0)

    model_config = ConfigDict(populate_by_name=True)


class PaymentPlanTemplateCreateRequest(BaseModel):
    productCode: str = Field(..., min_length=1, max_length=128)
    principal: float = Field(..., gt=0)
    discountRate: float = Field(..., ge=0)
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    isActive: bool = True
    installments: List[PaymentPlanInstallmentItem]

    model_config = ConfigDict(populate_by_name=True)


class PaymentPlanTemplateUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    principal: Optional[float] = Field(None, gt=0)
    discountRate: Optional[float] = Field(None, ge=0)
    metadata: Optional[dict[str, Any]] = None
    isActive: Optional[bool] = None
    installments: Optional[List[PaymentPlanInstallmentItem]] = None

    model_config = ConfigDict(populate_by_name=True)


class PaymentPlanInstallmentResponse(BaseModel):
    id: UUID
    period: int
    amount: float

    model_config = ConfigDict(populate_by_name=True)


class PaymentPlanTemplateResponse(BaseModel):
    id: UUID
    tenantId: UUID
    productCode: str
    name: Optional[str] = None
    description: Optional[str] = None
    principal: float
    discountRate: float
    metadata: Optional[dict[str, Any]] = None
    isActive: bool
    createdAt: datetime
    updatedAt: datetime
    installments: List[PaymentPlanInstallmentResponse]

    model_config = ConfigDict(populate_by_name=True)


UserUpdateRequest = UserPatch

