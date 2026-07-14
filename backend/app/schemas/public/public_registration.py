"""Schemas para registro público de tenants"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.services.facturas.validacion_service import validar_nit_guatemala


class TenantRequestCreate(BaseModel):
    """Schema para solicitar registro de un nuevo tenant"""
    company_name: str = Field(..., min_length=2, max_length=255)
    nit: str = Field(..., min_length=7, max_length=15)
    contact_name: str = Field(..., min_length=2, max_length=255)
    contact_email: EmailStr
    contact_phone: str | None = Field(None, max_length=20)
    regimen_fiscal_id: int | None = None
    estimated_clients_count: int | None = Field(None, ge=1, le=1000)
    notes: str | None = Field(None, max_length=1000)

    @field_validator('nit')
    @classmethod
    def validate_nit(cls, v: str) -> str:
        if not validar_nit_guatemala(v):
            raise ValueError('NIT inválido')
        return v.replace(" ", "").replace("-", "").upper()

class TenantRequestResponse(BaseModel):
    """Respuesta después de crear una solicitud"""
    id: int
    public_id: UUID
    company_name: str
    nit: str
    contact_name: str
    contact_email: EmailStr
    status: str
    created_at: datetime
    message: str = "Solicitud recibida. Será revisada en 24-48h hábiles."

    model_config = {"from_attributes": True}

class TenantRequestListResponse(BaseModel):
    """Respuesta para listar solicitudes (SuperAdmin)"""
    id: int
    public_id: UUID
    company_name: str
    nit: str
    contact_name: str
    contact_email: EmailStr
    contact_phone: str | None = None
    regimen_fiscal_id: int | None = None
    estimated_clients_count: int | None = None
    status: str
    notes: str | None = None
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

class TenantApprovalPayload(BaseModel):
    """Payload para aprobar una solicitud"""
    admin_email: EmailStr
    admin_password: str | None = None
    admin_full_name: str = Field(..., min_length=2, max_length=255)
    plan: str = Field(default="freemium", pattern="^(freemium|basic|pro|enterprise)$")
    max_usuarios: int = Field(default=3, ge=1, le=1000)
    trial_days: int | None = Field(None, ge=1, le=365)
    trial_max_usuarios: int | None = Field(None, ge=1, le=1000)

class TenantRejectionPayload(BaseModel):
    """Payload para rechazar una solicitud"""
    reason: str = Field(..., min_length=5, max_length=500)