# app/schemas/tenant.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.services.facturas.validacion_service import validar_nit_guatemala


class TenantCreate(BaseModel):
    """Schema para crear un nuevo tenant."""
    tenant_name: str = Field(..., min_length=2, max_length=100)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)
    nit: str
    plan: str | None = "freemium"
    
    @field_validator('nit')
    @classmethod
    def validate_nit(cls, v: str) -> str:
        if not validar_nit_guatemala(v):
            raise ValueError(
                'El NIT no es válido. Formatos aceptados:\n'
                '- NIT tradicional: 1234567-8, 12345678-9\n'
                '- NIT personal (9 dígitos): 123456789\n'
                '- CUI completo (13 dígitos) o CUI truncado (9-10 dígitos sin dígito verificador)'
            )
        return v.replace(" ", "").replace("-", "").upper()


class TenantResponse(BaseModel):
    """
    Schema de respuesta segura (nunca devuelve contraseñas).
    ✅ Exponemos public_id (UUID) en lugar de id (BIGINT).
    ✅ Eliminamos max_empresas (ya no es el límite comercial).
    """
    id: UUID  # ✅ Ahora es public_id (UUID)
    name: str
    nit: str
    schema_name: str
    plan: str
    max_usuarios: int  # ✅ Único límite comercial
    is_active: bool
    created_at: datetime
    admin_email: EmailStr | None = None
    
    # 🆕 Campos de trial (opcionales)
    trial_until: datetime | None = None
    trial_max_usuarios: int | None = None
    
    model_config = {"from_attributes": True}


class TenantStatusUpdate(BaseModel):
    """Para activar/suspender un tenant."""
    is_active: bool


class TenantTrialRequest(BaseModel):
    """
    Schema para activar/extender el trial de un tenant.
    Solo accesible para superadmin.
    """
    trial_days: int = Field(
        ...,
        gt=0,
        le=365,
        description="Días de duración del trial (1-365)"
    )
    trial_max_usuarios: int = Field(
        ...,
        gt=0,
        le=1000,
        description="Límite de usuarios durante el trial"
    )


class TenantUpgradeRequest(BaseModel):
    """
    Schema para hacer upgrade permanente del plan de un tenant.
    Solo accesible para superadmin.
    """
    max_usuarios: int = Field(
        ...,
        gt=0,
        description="Nuevo límite permanente de usuarios"
    )
    plan: str = Field(
        default="basic",
        pattern="^(freemium|basic|pro|enterprise)$",
        description="Plan comercial del tenant"
    )


class TenantUsageResponse(BaseModel):
    """
    Respuesta con el uso actual del tenant (usuarios, empresas, etc.)
    """
    tenant_id: UUID
    tenant_name: str
    plan: str
    usage: dict
    trial: dict
    warnings: list[str]
