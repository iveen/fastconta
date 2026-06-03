from uuid import UUID

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_name: str
    role: str
    full_name: str

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