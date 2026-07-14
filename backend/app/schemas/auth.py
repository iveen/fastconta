from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_name: str | None = None
    role: str | None = None
    full_name: str
    email: str
    user_id: int
    public_id: str
    must_change_password: bool = False
    password_expires_at: str | None = None

    model_config = {"json_schema_extra": {"example": {
        "access_token": "eyJ...",
        "token_type": "bearer",
        "tenant_name": "Mi Empresa",
        "role": "tenant_manager",
        "full_name": "Juan Pérez",
        "email": "juan@empresa.com",
        "user_id": 123,
        "public_id": "550e8400-e29b-41d4-a716-446655440000",
        "must_change_password": False,
        "password_expires_at": "2026-10-11T12:00:00Z"
    }}}
    

class SignupRequest(BaseModel):
    # Datos del Tenant / Despacho
    tenant_name: str
    nit: str
    
    # Datos del primer usuario (Administrador)
    admin_email: EmailStr
    admin_full_name: str
    admin_password: str

class SignupResponse(BaseModel):
    tenant_id: UUID
    schema_name: str
    admin_user_id: UUID
    message: str

    class Config:
        from_attributes = True

class ChangePasswordRequest(BaseModel):
    """Solicitud para cambiar contraseña."""
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validación básica en el schema (longitud)."""
        if len(v) < 12:
            raise ValueError('La contraseña debe tener al menos 12 caracteres')
        if len(v) > 72:
            raise ValueError('La contraseña no puede tener más de 72 caracteres')
        return v
    

class RequestPasswordResetRequest(BaseModel):
    email: EmailStr


class RequestPasswordResetResponse(BaseModel):
    message: str


class ConfirmPasswordResetRequest(BaseModel):
    token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=12, max_length=72)


class ConfirmPasswordResetResponse(BaseModel):
    message: str
    email: str

class LoginAuditFilter(BaseModel):
    user_id: int | None = None
    email: str | None = None
    status: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    limit: int = 100

class LoginAuditResponse(BaseModel):
    id: int
    user_id: int | None
    email_attempted: str
    ip_address: str | None
    user_agent: str | None
    status: str
    failure_reason: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginAuditStats(BaseModel):
    total_logins: int
    successful: int
    failed: int
    locked: int
    unique_users: int
    unique_ips: int
    most_failed_emails: list[dict]  # Top 5 emails con más fallos
    hourly_distribution: list[dict]  # Logins por hora (últimas 24h)

class FirstLoginChangePasswordRequest(BaseModel):
    """
    Solicitud para cambiar contraseña en el PRIMER login.
    NO requiere current_password porque el usuario acaba de autenticarse 
    con la contraseña temporal y el sistema lo fuerza a cambiarla.
    """
    new_password: str = Field(..., description="Nueva contraseña")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 12:
            raise ValueError('La contraseña debe tener al menos 12 caracteres')
        if len(v) > 72:
            raise ValueError('La contraseña no puede tener más de 72 caracteres')
        return v