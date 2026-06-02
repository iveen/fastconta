# app/schemas/user.py
from uuid import UUID

from pydantic import BaseModel, Field


class EmpresaAssignRequest(BaseModel):
    empresa_id: UUID

class UserCreateRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=72)
    full_name: str
    role: str = "tenant_member"
    tenant_id: UUID | None = None  # 🔹 Solo usado por superadmin