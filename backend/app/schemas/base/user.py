# app/schemas/user.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class EmpresaAssignRequest(BaseModel):
    empresa_id: UUID

class UserCreateRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=72)
    full_name: str
    role: str = "tenant_member"
    tenant_id: UUID | None = None  # 🔹 Solo usado por superadmin

"""Schemas para gestión de usuarios"""
class UserCreate(BaseModel):
    """
    Schema para crear un nuevo usuario.
    ⚠️ No incluye password: se genera automáticamente y se envía por email.
    """
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    full_name: str = Field(..., min_length=2, max_length=255, description="Nombre completo")
    role: str = Field(
        ...,
        pattern="^(superadmin|tenant_manager|tenant_member|tenant_client)$",
        description="Rol del usuario"
    )
    tenant_id: int | None = Field(
        None,
        description="ID del tenant (requerido solo para superadmin)"
    )


class UserResponse(BaseModel):
    """
    Schema de respuesta para información de usuario.
    No incluye información sensible como hashed_password.
    """
    id: int
    public_id: UUID
    email: EmailStr
    full_name: str
    role: str | None = None
    tenant_id: int | None = None
    is_active: bool
    is_locked: bool = False
    must_change_password: bool = False
    password_expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    @field_validator('role', mode='before')
    @classmethod
    def extract_role_code(cls, v):
        """
        Extrae el código del rol si es un objeto SQLAlchemy, 
        o lo devuelve si ya es un string.
        """
        if hasattr(v, 'codigo'):
            return v.codigo
        if isinstance(v, str):
            return v
        return str(v) if v else None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema para listar usuarios (versión simplificada)"""
    id: int
    public_id: UUID
    email: EmailStr
    full_name: str
    role: str | None = None
    is_active: bool
    created_at: datetime

    @field_validator('role', mode='before')
    @classmethod
    def extract_role_code(cls, v):
        if hasattr(v, 'codigo'):
            return v.codigo
        if isinstance(v, str):
            return v
        return str(v) if v else None

    class Config:
        from_attributes = True