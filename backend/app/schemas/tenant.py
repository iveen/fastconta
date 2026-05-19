from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID

class TenantCreate(BaseModel):
    tenant_name: str
    admin_email: EmailStr
    admin_password: str

class TenantResponse(BaseModel):
    id: UUID
    name: str
    schema_name: str
    created_at: datetime