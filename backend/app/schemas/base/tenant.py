"""
Schemas unificados para gestión de Tenants.
Incluye: registro público, aprobación, gestión directa, suscripciones, trials y uso.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.services.facturas.validacion_service import validar_nit_guatemala


# ============================================================
# VALIDADORES COMPARTIDOS
# ============================================================
def validate_nit_guatemala_field(v: str) -> str:
    """Validador reutilizable para NIT guatemalteco"""
    if not validar_nit_guatemala(v):
        raise ValueError(
            "El NIT no es válido. Formatos aceptados:\n"
            "- NIT tradicional: 1234567-8, 12345678-9\n"
            "- NIT personal (9 dígitos): 123456789\n"
            "- CUI completo (13 dígitos) o CUI truncado (9-10 dígitos sin dígito verificador)"
        )
    return v.replace(" ", "").replace("-", "").upper()


# ============================================================
# SCHEMAS PARA REGISTRO PÚBLICO (Solicitudes)
# ============================================================

class TenantRequestCreate(BaseModel):
    """Schema para solicitar registro de un nuevo tenant (formulario público)"""
    company_name: str = Field(..., min_length=2, max_length=255)
    nit: str = Field(..., min_length=7, max_length=15)
    contact_name: str = Field(..., min_length=2, max_length=255)
    contact_email: EmailStr
    contact_phone: str | None = Field(None, max_length=20)
    regimen_fiscal_id: int | None = None
    estimated_clients_count: int | None = Field(None, ge=1, le=1000)
    notes: str | None = Field(None, max_length=1000)

    @field_validator("nit")
    @classmethod
    def validate_nit(cls, v: str) -> str:
        return validate_nit_guatemala_field(v)


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
    """
    Payload para aprobar una solicitud.
    Incluye configuración inicial del tenant y suscripción.
    """
    admin_email: EmailStr
    admin_password: str | None = Field(None, min_length=8)
    admin_full_name: str = Field(..., min_length=2, max_length=255)
    
    # Configuración de plan
    plan: str = Field(default="freemium", pattern="^(freemium|basico|profesional|empresarial)$")
    max_concurrent_sessions: int = Field(default=1, ge=1, le=100)
    max_users_registered: int = Field(default=3, ge=1, le=1000)
    
    # Trial (opcional)
    trial_days: int | None = Field(None, ge=1, le=365)
    trial_max_concurrent_sessions: int | None = Field(None, ge=1, le=100)
    trial_max_users_registered: int | None = Field(None, ge=1, le=1000)
    
    billing_cycle: str = Field(default="monthly", pattern="^(monthly|quarterly|yearly)$")


class TenantRejectionPayload(BaseModel):
    """Payload para rechazar una solicitud"""
    reason: str = Field(..., min_length=5, max_length=500)


# ============================================================
# SCHEMAS PARA GESTIÓN DIRECTA DE TENANTS (SuperAdmin)
# ============================================================

class TenantCreate(BaseModel):
    """
    Schema para crear un nuevo tenant directamente (SuperAdmin).
    Usado cuando se crea desde el panel de administración.
    """
    tenant_name: str = Field(..., min_length=2, max_length=100)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)
    nit: str
    
    # Configuración inicial
    plan: str | None = Field(default="freemium", pattern="^(freemium|basico|profesional|empresarial)$")
    max_concurrent_sessions: int = Field(default=1, ge=1, le=100)
    max_users_registered: int = Field(default=3, ge=1, le=1000)

    @field_validator("nit")
    @classmethod
    def validate_nit(cls, v: str) -> str:
        return validate_nit_guatemala_field(v)


class TenantResponse(BaseModel):
    """
    Schema de respuesta segura para tenant.
    ✅ Exponemos public_id (UUID) en lugar de id (BIGINT).
    ✅ Incluye información de suscripción activa.
    """
    id: int
    public_id: UUID
    name: str
    nit: str
    schema_name: str
    is_active: bool
    created_at: datetime
    admin_email: EmailStr | None = None
    
    # Información de suscripción activa
    active_subscription: dict | None = None
    # {
    #   "plan_type": "profesional",
    #   "max_concurrent_sessions": 5,
    #   "max_users_registered": 10,
    #   "status": "active",
    #   "current_period_end": "2026-08-27T00:00:00Z",
    #   "days_remaining": 31
    # }
    
    # Uso actual
    current_usage: dict | None = None
    # {
    #   "active_sessions": 2,
    #   "total_users": 5
    # }

    model_config = {"from_attributes": True}


class TenantStatusUpdate(BaseModel):
    """Para activar/suspender un tenant."""
    is_active: bool


# ============================================================
# SCHEMAS PARA SUSCRIPCIONES
# ============================================================

class TenantSubscriptionCreate(BaseModel):
    """
    Schema para crear una suscripción inicial para un tenant.
    Usado al aprobar una solicitud o crear tenant directamente.
    """
    plan_type: str = Field(
        ..., 
        pattern="^(freemium|basico|profesional|empresarial)$",
        description="Tipo de plan comercial"
    )
    max_concurrent_sessions: int = Field(
        ..., 
        ge=1, 
        le=100,
        description="Límite de sesiones concurrentes permitidas"
    )
    max_users_registered: int = Field(
        ..., 
        ge=1, 
        le=1000,
        description="Límite de usuarios registrados en el sistema"
    )
    billing_cycle: str = Field(
        default="monthly", 
        pattern="^(monthly|quarterly|yearly)$",
        description="Ciclo de facturación"
    )
    trial_days: int = Field(
        default=0, 
        ge=0, 
        le=365,
        description="Días de período de prueba (0 = sin trial)"
    )
    billing_email: EmailStr | None = Field(
        None, 
        description="Email para facturación (si es diferente al admin)"
    )
    nit_facturacion: str | None = Field(
        None, 
        max_length=15,
        description="NIT para facturación"
    )

    @field_validator("nit_facturacion")
    @classmethod
    def validate_nit_facturacion(cls, v: str | None) -> str | None:
        if v:
            return validate_nit_guatemala_field(v)
        return v


class TenantSubscriptionUpdate(BaseModel):
    """
    Schema para actualizar completamente una suscripción existente.
    Solo accesible para superadmin.
    """
    plan_type: str = Field(
        ..., 
        pattern="^(freemium|basico|profesional|empresarial)$",
        description="Nuevo tipo de plan comercial"
    )
    max_concurrent_sessions: int = Field(
        ..., 
        ge=1, 
        le=100,
        description="Nuevo límite de sesiones concurrentes"
    )
    max_users_registered: int = Field(
        ..., 
        ge=1, 
        le=1000,
        description="Nuevo límite de usuarios registrados"
    )
    billing_cycle: str = Field(
        default="monthly", 
        pattern="^(monthly|quarterly|yearly)$",
        description="Ciclo de facturación"
    )
    trial_days: int | None = Field(
        None, 
        ge=0, 
        le=365,
        description="Días de trial a agregar (si aplica)"
    )


class TenantSubscriptionUpgrade(BaseModel):
    """
    Schema para hacer upgrade incremental de una suscripción.
    Solo se pueden aumentar los límites, no disminuir.
    Solo accesible para superadmin.
    """
    max_concurrent_sessions: int | None = Field(
        None, 
        ge=1, 
        le=100,
        description="Nuevo límite de sesiones concurrentes (debe ser mayor al actual)"
    )
    max_users_registered: int | None = Field(
        None, 
        ge=1, 
        le=1000,
        description="Nuevo límite de usuarios registrados (debe ser mayor al actual)"
    )
    plan_type: str | None = Field(
        None, 
        pattern="^(freemium|basico|profesional|empresarial)$",
        description="Nuevo plan comercial (opcional)"
    )


# ============================================================
# 🆕 SCHEMAS PARA TRIAL Y UPGRADE (Compatibilidad con endpoints existentes)
# ============================================================

class TenantTrialRequest(BaseModel):
    """
    Schema para activar/extender el trial de un tenant.
    Solo accesible para superadmin.
    
    🔄 Adaptado al nuevo modelo de sesiones concurrentes.
    """
    trial_days: int = Field(
        ..., 
        gt=0, 
        le=365, 
        description="Días de duración del trial (1-365)"
    )
    trial_max_concurrent_sessions: int = Field(
        ..., 
        gt=0, 
        le=100, 
        description="Límite de sesiones concurrentes durante el trial"
    )
    trial_max_users_registered: int = Field(
        ..., 
        gt=0, 
        le=1000, 
        description="Límite de usuarios registrados durante el trial"
    )


class TenantUpgradeRequest(BaseModel):
    """
    Schema para hacer upgrade permanente del plan de un tenant.
    Solo accesible para superadmin.
    
    🔄 Adaptado al nuevo modelo de sesiones concurrentes.
    """
    max_concurrent_sessions: int = Field(
        ..., 
        gt=0, 
        le=100,
        description="Nuevo límite permanente de sesiones concurrentes"
    )
    max_users_registered: int = Field(
        ..., 
        gt=0, 
        le=1000,
        description="Nuevo límite permanente de usuarios registrados"
    )
    plan: str = Field(
        default="basico", 
        pattern="^(freemium|basico|profesional|empresarial)$", 
        description="Plan comercial del tenant"
    )


# ============================================================
# SCHEMAS PARA USO Y DASHBOARD
# ============================================================

class TenantUsageResponse(BaseModel):
    """
    Respuesta con el uso actual del tenant (sesiones, usuarios, suscripción).
    """
    tenant_id: UUID
    tenant_name: str
    subscription: dict
    usage: dict
    warnings: list[str]


class TenantDashboardResponse(BaseModel):
    """
    Respuesta para el dashboard del tenant_manager.
    Muestra información de su suscripción y uso.
    """
    tenant_name: str
    plan_type: str
    subscription_status: str
    days_remaining: int | None
    
    limits: dict
    # {
    #   "max_concurrent_sessions": 5,
    #   "max_users_registered": 10
    # }
    
    current_usage: dict
    # {
    #   "active_sessions": 2,
    #   "total_users": 5
    # }
    
    warnings: list[str]
