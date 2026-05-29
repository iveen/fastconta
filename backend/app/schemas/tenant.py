# app/schemas/tenant.py
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional
from app.services.validation_service import validar_nit_guatemala


class TenantCreate(BaseModel):
    tenant_name: str
    admin_email: EmailStr
    admin_password: str
    nit: str
    plan: Optional[str] = "freemium"

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
    """Esquema de respuesta segura (nunca devuelve contraseñas ni datos sensibles)."""
    id: UUID
    name: str
    nit: str
    schema_name: str
    plan: str
    max_empresas: int
    max_usuarios: int
    is_active: bool
    created_at: datetime
    admin_email: Optional[EmailStr] = None

    model_config = {"from_attributes": True}  # Compatibilidad con SQLAlchemy


class TenantStatusUpdate(BaseModel):
    """Para activar/suspender un tenant."""
    is_active: bool