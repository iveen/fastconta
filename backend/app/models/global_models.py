import enum
from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from app.db.base import Base
from app.db.mixins import AuditableFull, BigIntPKMixin, SoftDelete
from app.db.session import AsyncSession


class Tenant(BigIntPKMixin, AuditableFull, SoftDelete, Base):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "public"}

    name = Column(String(255), nullable=False)
    nit = Column(String(15), unique=True, nullable=False)
    schema_name = Column(String(63), unique=True, nullable=False)
    admin_email = Column(String(255), nullable=True)
    
    # ✅ Campos "efectivos" - caché del valor actual de la suscripción
    # Se actualizan automáticamente cuando cambia TenantSubscription
    plan = Column(String(20), default="freemium", nullable=False, index=True)
    max_concurrent_sessions = Column(Integer, default=1, nullable=False)
    max_users_registered = Column(Integer, default=3, nullable=False)

    # Relaciones
    subscriptions = relationship(
        "TenantSubscription",
        back_populates="tenant",
        cascade="all, delete-orphan",
        order_by="desc(TenantSubscription.current_period_start)"
    )
    
    sessions = relationship(
        "SessionAudit",
        back_populates="tenant",
        foreign_keys="[SessionAudit.tenant_id]",
        cascade="all, delete-orphan"
    )
    
    users = relationship(
        "User",
        back_populates="tenant",
        foreign_keys="[User.tenant_id]",
    )
    
    empresas = relationship(
        "Empresa", 
        back_populates="tenant", 
        foreign_keys="[Empresa.tenant_id]", 
        cascade="all, delete-orphan"
    )

    # ============================================================
    # MÉTODOS HELPER
    # ============================================================
    
    def get_active_subscription(self) -> "TenantSubscription | None":
        """Retorna la suscripción activa del tenant"""
        now = datetime.now(timezone.utc)
        
        for sub in self.subscriptions:
            if sub.is_active and sub.current_period_start <= now <= sub.current_period_end:
                return sub
        
        return self.subscriptions[0] if self.subscriptions else None
    
    def is_trial_active(self) -> bool:
        """Verifica si el tenant tiene un trial activo"""
        sub = self.get_active_subscription()
        return sub.is_trial if sub else False
    
    def trial_days_remaining(self) -> int | None:
        """Retorna los días restantes del trial"""
        sub = self.get_active_subscription()
        return sub.days_remaining if sub and sub.is_trial else None
    
    def sync_from_subscription(self):
        """
        Sincroniza los campos efectivos del tenant con la suscripción activa.
        Llamar después de crear/actualizar TenantSubscription.
        """
        sub = self.get_active_subscription()
        if sub:
            self.plan = sub.plan_type
            self.max_concurrent_sessions = sub.max_concurrent_sessions
            self.max_users_registered = sub.max_users_registered
    
    @staticmethod
    async def count_active_users(db: AsyncSession, tenant_id: int) -> int:
        """Cuenta usuarios activos del tenant (optimizado)"""
        from sqlalchemy import func, select
        count = await db.scalar(
            select(func.count(User.id)).where(
                User.tenant_id == tenant_id,
                User.is_active.is_(True),
                User.is_deleted.is_(False),
            )
        )
        return count or 0
    
    @staticmethod
    async def count_active_sessions(db: AsyncSession, tenant_id: int) -> int:
        """Cuenta sesiones activas del tenant (últimos 15 min)"""

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
        count = await db.scalar(
            select(func.count(SessionAudit.id)).where(
                SessionAudit.tenant_id == tenant_id,
                SessionAudit.is_active.is_(True),
                SessionAudit.last_activity >= cutoff
            )
        )
        return count or 0
    
    async def can_add_user(self, db: AsyncSession) -> bool:
        """Verifica si se puede agregar más usuarios"""
        count = await self.count_active_users(db, self.id)
        return count < self.max_users_registered
    
    async def can_create_session(self, db: AsyncSession) -> bool:
        """Verifica si se puede crear una nueva sesión concurrente"""
        count = await self.count_active_sessions(db, self.id)
        return count < self.max_concurrent_sessions
    
    async def get_usage_summary(self, db: AsyncSession) -> dict:
        """Retorna resumen de uso completo (para dashboard)"""
        users_count = await self.count_active_users(db, self.id)
        sessions_count = await self.count_active_sessions(db, self.id)
        
        return {
            "users": {
                "actual": users_count,
                "limite": self.max_users_registered,
                "disponibles": max(0, self.max_users_registered - users_count),
                "porcentaje": round((users_count / self.max_users_registered * 100) if self.max_users_registered > 0 else 0, 1)
            },
            "sessions": {
                "actual": sessions_count,
                "limite": self.max_concurrent_sessions,
                "disponibles": max(0, self.max_concurrent_sessions - sessions_count),
                "porcentaje": round((sessions_count / self.max_concurrent_sessions * 100) if self.max_concurrent_sessions > 0 else 0, 1)
            },
            "trial": {
                "activo": self.is_trial_active(),
                "dias_restantes": self.trial_days_remaining()
            }
        }


class RegistrationAttempt(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "registration_attempts"
    __table_args__ = {"schema": "public"}
    ip_address = Column(String(45), nullable=False)


# ============================================================
# TENANT SUBSCRIPTION MODELS
# ============================================================

class SubscriptionStatus(str, enum.Enum):
    active = "activa"
    trial = "prueba"
    expired = "expirada"
    cancelled = "cancelada"
    suspended = "suspendida"

class BillingCycle(str, enum.Enum):
    monthly = "mensual"
    quarterly = "trimestral"
    yearly = "anual"

class TenantSubscription(BigIntPKMixin, AuditableFull, Base):
    """
    Suscripción del tenant - Maneja planes, límites y facturación
    """
    __tablename__ = "tenant_subscriptions"
    __table_args__ = (
        Index("idx_tenant_subscriptions_tenant", "tenant_id"),
        Index("idx_tenant_subscriptions_status", "status"),
        Index("idx_tenant_subscriptions_period", "current_period_start", "current_period_end"),
        UniqueConstraint("tenant_id", "current_period_start", name="uq_tenant_active_subscription"),
        {"schema": "public"},
    )
    
    # Relación con tenant
    tenant_id = Column(BigInteger, ForeignKey("public.tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Información del plan
    plan_type = Column(String(20), nullable=False, index=True)
    # freemium, basico, profesional, empresarial
    
    # Límites
    max_concurrent_sessions = Column(Integer, nullable=False, default=1)
    max_users_registered = Column(Integer, nullable=False, default=1)
    # Usuarios que pueden estar registrados (no concurrentes)
    
    # Precios
    price_per_user = Column(Numeric(10, 2), nullable=False, server_default="0.00")
    base_price = Column(Numeric(10, 2), nullable=False, server_default="0.00")
    total_monthly_price = Column(Numeric(10, 2), nullable=False, server_default="0.00")
    
    # Ciclo de facturación
    billing_cycle = Column(String(20), nullable=False, default=BillingCycle.monthly.value)
    
    # Período actual
    current_period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    current_period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Estado
    status = Column(String(20), nullable=False, default=SubscriptionStatus.trial.value, index=True)
    
    # Información de pago
    payment_method = Column(String(50), nullable=True)
    # tarjeta, transferencia, pendiente
    last_payment_date = Column(DateTime(timezone=True), nullable=True)
    last_payment_amount = Column(Numeric(10, 2), nullable=True)
    next_billing_date = Column(DateTime(timezone=True), nullable=True)
    
    # Facturación
    billing_email = Column(String(255), nullable=True)
    billing_address = Column(Text, nullable=True)
    nit_facturacion = Column(String(15), nullable=True)
    
    # Metadatos
    stripe_subscription_id = Column(String(255), nullable=True)
    # Si usas Stripe en el futuro
    notes = Column(Text, nullable=True)
    
    # Relaciones
    tenant = relationship("Tenant", back_populates="subscriptions")
    usage_logs = relationship("SubscriptionUsageLog", back_populates="subscription", cascade="all, delete-orphan")
    
    # ============================================================
    # MÉTODOS HELPER
    # ============================================================
    
    @property
    def is_active(self) -> bool:
        """Verifica si la suscripción está activa"""
        return self.status in [SubscriptionStatus.active.value, SubscriptionStatus.trial.value]
    
    @property
    def is_trial(self) -> bool:
        """Verifica si está en período de prueba"""
        return self.status == SubscriptionStatus.trial.value
    
    @property
    def days_remaining(self) -> int:
        """Días restantes del período actual"""
        delta = self.current_period_end - datetime.now(timezone.utc)
        return max(0, delta.days)
    
    @property
    def is_expired(self) -> bool:
        """Verifica si el período ha expirado"""
        return datetime.now(datetime.timezone.utc) > self.current_period_end
    
    def calculate_total_price(self) -> float:
        """Calcula el precio total basado en usuarios y ciclo de facturación"""
        base = float(self.base_price or 0)
        per_user = float(self.price_per_user or 0)
        users = self.max_users_registered
        
        monthly_total = base + (per_user * users)
        
        # Aplicar descuento según ciclo
        if self.billing_cycle == BillingCycle.quarterly.value:
            return monthly_total * 3 * 0.95  # 5% descuento
        elif self.billing_cycle == BillingCycle.yearly.value:
            return monthly_total * 12 * 0.80  # 20% descuento
        
        return monthly_total
    
    def renew_period(self, new_status: str = None):
        """Renueva el período de suscripción"""
        
        self.current_period_start = self.current_period_end
        self.current_period_end = self.current_period_start + timedelta(days=30)
        
        if new_status:
            self.status = new_status
        
        self.total_monthly_price = self.calculate_total_price()
    
    def upgrade_plan(self, new_plan: str, new_max_sessions: int, new_price_per_user: float):
        """Actualiza el plan de suscripción"""
        self.plan_type = new_plan
        self.max_concurrent_sessions = new_max_sessions
        self.price_per_user = new_price_per_user
        self.total_monthly_price = self.calculate_total_price()


class SubscriptionUsageLog(BigIntPKMixin, Base):
    """
    Log de uso de la suscripción - Para tracking y facturación
    """
    __tablename__ = "subscription_usage_logs"
    __table_args__ = (
        Index("idx_usage_logs_subscription", "subscription_id"),
        Index("idx_usage_logs_date", "logged_at"),
        {"schema": "public"},
    )
    
    subscription_id = Column(BigInteger, ForeignKey("public.tenant_subscriptions.id", ondelete="CASCADE"), nullable=False)
    
    # Métricas
    concurrent_sessions_used = Column(Integer, nullable=False, default=0)
    total_users_registered = Column(Integer, nullable=False, default=0)
    peak_concurrent_sessions = Column(Integer, nullable=False, default=0)
    
    # Timestamp
    logged_at = Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    
    # Metadatos
    session_details = Column(JSONB, nullable=True)
    # Información detallada de sesiones activas
    
    # Relaciones
    subscription = relationship("TenantSubscription", back_populates="usage_logs")


class SessionAudit(BigIntPKMixin, AuditableFull, Base):
    """
    Auditoría de sesiones - Tracking de login/logout
    """
    __tablename__ = "session_audit"
    __table_args__ = (
        Index("idx_session_audit_user", "user_id"),
        Index("idx_session_audit_tenant", "tenant_id"),
        Index("idx_session_audit_session", "session_token", unique=True),
        Index("idx_session_audit_active", "is_active", "last_activity"),
        {"schema": "public"},
    )
    
    user_id = Column(BigInteger, ForeignKey("public.users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(BigInteger, ForeignKey("public.tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Sesión
    session_token = Column(String(500), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    last_activity = Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Información del dispositivo
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_info = Column(JSONB, nullable=True)
    # {browser: "Chrome", os: "Windows", device_type: "desktop"}
    
    # Metadata
    login_method = Column(String(20), nullable=True)
    # password, oauth, api_key
    logout_reason = Column(String(50), nullable=True)
    # user_logout, timeout, admin_terminated, expired
    
    # Relaciones
    user = relationship("User", foreign_keys=[user_id])
    tenant = relationship("Tenant", foreign_keys=[tenant_id])

# ============================================================
# TENANT REQUESTS - Solicitudes de registro público
# ============================================================
class TenantRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class TenantRequest(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "tenant_requests"
    __table_args__ = {"schema": "public"}

    company_name = Column(String(255), nullable=False)
    nit = Column(String(15), nullable=False, index=True)
    contact_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False, index=True)
    contact_phone = Column(String(20), nullable=True)

    regimen_fiscal_id = Column(BigInteger, ForeignKey("public.regimenes_fiscales.id"), nullable=True)
    estimated_clients_count = Column(Integer, nullable=True)

    status = Column(String(20), nullable=False, default=TenantRequestStatus.pending.value, index=True)
    reviewed_by = Column(BigInteger, ForeignKey("public.users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    regimen_fiscal = relationship("RegimenFiscal", foreign_keys=[regimen_fiscal_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


# ============================================================
# CATÁLOGOS SIMPLES - CON SoftDelete
# ============================================================
class TipoDTE(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "tipos_dte"
    __table_args__ = {"schema": "public"}
    codigo = Column(String(10), unique=True, nullable=False, index=True)
    descripcion = Column(String(100), nullable=False)
    requiere_complemento = Column(Boolean, default=False, nullable=False)
    es_factura = Column(Boolean, default=True, nullable=False)


class CatalogoMoneda(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "catalogo_monedas"
    __table_args__ = {"schema": "public"}
    codigo_banguat = Column(String(5), unique=True, nullable=False, index=True)
    codigo_iso = Column(String(3), unique=True, nullable=False, index=True)
    nombre = Column(String(50), nullable=False)
    simbolo = Column(String(5), nullable=True)
    decimales = Column(Integer, default=2, nullable=False)


class CatalogoImpuestoEspecial(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "catalogo_impuestos_especiales"
    __table_args__ = {"schema": "public"}
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)


class TipoLibro(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "tipos_libro"
    __table_args__ = {"schema": "public"}
    codigo = Column(String(50), nullable=False)
    nombre = Column(String(255), nullable=False, unique=True)


class EstadoLibro(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "estados_libro"
    __table_args__ = {"schema": "public"}
    nombre = Column(String(50), nullable=False)


class TipoPersona(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "tipos_persona"
    __table_args__ = {"schema": "public"}
    nombre = Column(String(50), nullable=False, unique=True)
    descripcion = Column(String(200), nullable=True)


class TipoDomicilio(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "tipos_domicilio"
    __table_args__ = {"schema": "public"}
    nombre = Column(String(50), nullable=False, unique=True)


class Departamento(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "departamentos"
    __table_args__ = {"schema": "public"}
    codigo_iso = Column(String(2), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    municipios = relationship("Municipio", back_populates="departamento")


class Municipio(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "municipios"
    __table_args__ = {"schema": "public"}
    codigo_iso = Column(String(4), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    departamento_id = Column(BigInteger, ForeignKey("public.departamentos.id"), nullable=False)
    departamento = relationship("Departamento", back_populates="municipios")


class ActividadEconomicaSAT(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "actividades_economicas_sat"
    __table_args__ = {"schema": "public"}
    codigo_sat = Column(String(20), unique=True, nullable=False, index=True)
    nombre_actividad = Column(String(255), nullable=False)
    seccion = Column(String(255), nullable=True)


# ============================================================
# RBAC - CON SoftDelete
# ============================================================
class Role(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "public"}
    codigo = Column(String(30), unique=True, nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    nivel_acceso = Column(Integer, nullable=False)


class User(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    tenant_id = Column(BigInteger, ForeignKey("public.tenants.id"), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role_id = Column(BigInteger, ForeignKey("public.roles.id"), nullable=False)

    # Política de contraseñas
    must_change_password = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Indica si el usuario debe cambiar su contraseña en el próximo login",
    )
    password_changed_at = Column(
        DateTime(timezone=True), nullable=True, comment="Fecha del último cambio de contraseña"
    )
    password_expires_at = Column(
        DateTime(timezone=True), nullable=True, comment="Fecha de expiración de la contraseña (90 días)"
    )

    # ✅ NUEVO: Política de bloqueo por intentos fallidos
    failed_login_attempts = Column(
        Integer, default=0, nullable=False, comment="Contador de intentos fallidos consecutivos"
    )
    locked_until = Column(
        DateTime(timezone=True), nullable=True, comment="Fecha hasta la cual el usuario está bloqueado"
    )
    is_locked = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Indica si el usuario está bloqueado (por intentos fallidos o admin)",
    )

    tenant = relationship("Tenant", back_populates="users", foreign_keys=[tenant_id])
    role = relationship("Role", foreign_keys=[role_id], lazy="selectin")
    empresas_asignadas = relationship(
        "UserEmpresa", back_populates="user", foreign_keys="[UserEmpresa.user_id]", cascade="all, delete-orphan"
    )


class UserEmpresa(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "user_empresas"
    __table_args__ = (
        UniqueConstraint("user_id", "tenant_id", "empresa_id", name="uq_user_empresa_tenant"),
        {"schema": "public"},
    )
    user_id = Column(BigInteger, ForeignKey("public.users.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(BigInteger, ForeignKey("public.tenants.id", ondelete="CASCADE"), nullable=False)
    empresa_id = Column(BigInteger, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    tenant = relationship("Tenant", foreign_keys=[tenant_id])


# ============================================================
# ACTIVOS FIJOS - Catálogo CON SoftDelete
# ============================================================
class EstadoActivoFijoEnum(str, enum.Enum):
    activo = "activo"
    totalmente_depreciado = "totalmente_depreciado"
    dado_baja = "dado_baja"
    vendido = "vendido"


class CategoriaActivoFijo(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "categorias_activos_fijos"
    __table_args__ = (
        CheckConstraint("tasa_maxima_anual >= tasa_minima_anual", name="chk_categoria_tasa_valida"),
        {"schema": "public"},
    )
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)
    tasa_minima_anual = Column(Numeric(5, 2), nullable=False, server_default="0.00")
    tasa_maxima_anual = Column(Numeric(5, 2), nullable=False)
    vida_util_meses_default = Column(Integer, nullable=False)
    codigo_prefijo = Column(String(10), nullable=False, unique=True, index=True)


# ============================================================
# MOTOR TRIBUTARIO - CON SoftDelete
# ============================================================
class RegimenFiscal(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "regimenes_fiscales"
    __table_args__ = {"schema": "public"}
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)

    configuraciones_impuestos = relationship(
        "RegimenImpuestoConfig", back_populates="regimen", cascade="all, delete-orphan"
    )
    formularios_sat = relationship(
        "FormularioSat", secondary="public.regimenes_formularios_sat", back_populates="regimenes"
    )


class CatalogoImpuesto(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "catalogo_impuestos"
    __table_args__ = {"schema": "public"}
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=False)
    tasa_porcentaje = Column(Numeric(5, 2), nullable=True)
    tasa_fija_monto = Column(Numeric(15, 2), nullable=True, server_default="0.00")
    limite_inferior = Column(Numeric(15, 2), nullable=True, server_default="0.00")
    limite_superior = Column(Numeric(15, 2), nullable=True)
    frecuencia_pago = Column(String(20), nullable=False)
    frecuencia_liquidacion = Column(String(20), nullable=False)
    es_acreditable = Column(Boolean, default=False, nullable=False)
    requiere_autorizacion_sat = Column(Boolean, default=False, nullable=False)


class RegimenImpuestoConfig(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "regimen_impuesto_config"
    __table_args__ = (
        UniqueConstraint("regimen_id", "impuesto_id", name="uq_regimen_impuesto_unico"),
        {"schema": "public"},
    )
    regimen_id = Column(BigInteger, ForeignKey("public.regimenes_fiscales.id"), nullable=False, index=True)
    impuesto_id = Column(BigInteger, ForeignKey("public.catalogo_impuestos.id"), nullable=False, index=True)

    tasa_porcentaje = Column(Numeric(5, 2), nullable=True)
    tasa_fija_monto = Column(Numeric(15, 2), nullable=True, server_default="0.00")
    limite_inferior = Column(Numeric(15, 2), nullable=True, server_default="0.00")
    limite_superior = Column(Numeric(15, 2), nullable=True)
    es_acreditable = Column(Boolean, default=False, nullable=False)
    es_retencion_definitiva = Column(Boolean, default=False, nullable=False)
    requiere_autorizacion_sat = Column(Boolean, default=False, nullable=False)

    regimen = relationship("RegimenFiscal", back_populates="configuraciones_impuestos")
    impuesto = relationship("CatalogoImpuesto")


class RegimenDteConfig(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "regimen_dte_config"
    __table_args__ = {"schema": "public"}
    regimen_id = Column(BigInteger, ForeignKey("public.regimenes_fiscales.id"), nullable=False)
    dte_id = Column(BigInteger, ForeignKey("public.tipos_dte.id"), nullable=False)
    es_exclusivo = Column(Boolean, default=False, nullable=False)

    regimen = relationship("RegimenFiscal")
    dte = relationship("TipoDTE")


# ============================================================
# FORMULARIOS SAT - CON SoftDelete
# ============================================================
class FormularioSat(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "formularios_sat"
    __table_args__ = (
        UniqueConstraint("codigo", "version", name="uq_formulario_codigo_version"),
        Index("idx_formularios_vigencia", "codigo", "fecha_vigencia_desde", "fecha_vigencia_hasta"),
        {"schema": "public"},
    )
    codigo = Column(String(20), nullable=False, index=True)
    version = Column(String(10), nullable=False, default="1.0")
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text)
    fecha_vigencia_desde = Column(Date, nullable=False, server_default=text("CURRENT_DATE"))
    fecha_vigencia_hasta = Column(Date, nullable=True)
    es_version_activa = Column(Boolean, default=True, server_default="true")
    editable = Column(Boolean, default=True, server_default="true", nullable=False)
    formulario_padre_id = Column(BigInteger, ForeignKey("public.formularios_sat.id"), nullable=True)

    secciones = relationship("SeccionFormulario", back_populates="formulario", cascade="all, delete-orphan")
    regimenes = relationship(
        "RegimenFiscal", secondary="public.regimenes_formularios_sat", back_populates="formularios_sat"
    )
    version_hija = relationship(
        "FormularioSat",
        back_populates="version_padre",
        foreign_keys=[formulario_padre_id],
        remote_side=[formulario_padre_id],
    )
    # ✅ CORREGIDO: Usar string en lugar de referencia directa
    version_padre = relationship(
        "FormularioSat",
        back_populates="version_hija",
        foreign_keys=[formulario_padre_id],
        remote_side="FormularioSat.id",  # ✅ String en lugar de [id]
    )

    @property
    def nombre_completo(self):
        return f"{self.codigo} v{self.version}"


class SeccionFormulario(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "secciones_formulario"
    __table_args__ = (
        UniqueConstraint("formulario_id", "numero_seccion", name="uq_seccion_formulario"),
        {"schema": "public"},
    )
    formulario_id = Column(BigInteger, ForeignKey("public.formularios_sat.id"), nullable=False)
    numero_seccion = Column(String(10), nullable=False)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text)
    orden = Column(Integer, nullable=False, default=0)
    tipo_seccion = Column(String(30), nullable=False)
    es_obligatoria = Column(Boolean, default=True, server_default="true")
    requiere_exportador = Column(Boolean, default=False, server_default="false")
    es_automatica = Column(Boolean, default=False, nullable=False, server_default="false")

    formulario = relationship("FormularioSat", back_populates="secciones")
    casillas = relationship("CasillaSat", back_populates="seccion_rel", cascade="all, delete-orphan")


class CasillaSat(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "casillas_sat"
    __table_args__ = (UniqueConstraint("seccion_id", "codigo", name="uq_casilla_seccion_codigo"), {"schema": "public"})
    seccion_id = Column(BigInteger, ForeignKey("public.secciones_formulario.id"), nullable=True)
    codigo = Column(String(50), nullable=False)
    codigo_visual = Column(String(20), nullable=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text)
    orden_seccion = Column(Integer, default=0)
    tipo_casilla = Column(String(30), nullable=False, default="CALCULO")
    naturaleza = Column(String(20), nullable=True)
    formula_calculo = Column(Text, nullable=True)
    porcentaje_aplicable = Column(Numeric(5, 2), nullable=True)
    campo_origen_factura = Column(String(50), nullable=True)
    es_editable = Column(Boolean, default=False, server_default="false")
    requiere_justificacion = Column(Boolean, default=False, server_default="false")
    es_visible_usuario = Column(Boolean, default=True, server_default="true")
    es_automatica = Column(Boolean, nullable=False, default=False, server_default="false")
    dependencias = Column(JSON, nullable=True)
    funcion_calculo = Column(String(50), nullable=True)
    parametros_funcion = Column(JSON, nullable=True)

    seccion_rel = relationship("SeccionFormulario", back_populates="casillas")
    reglas_filtrado = relationship("ReglaFiltradoFactura", back_populates="casilla", cascade="all, delete-orphan")
    exclusiones = relationship("ExclusionCasilla", back_populates="casilla", cascade="all, delete-orphan")
    detalles = relationship("DetalleDeclaracionImpuesto", back_populates="casilla")

    @property
    def seccion(self) -> str | None:
        if self.seccion_rel:
            return self.seccion_rel.numero_seccion
        return None

    @property
    def formulario_id(self):
        return self.seccion_rel.formulario_id if self.seccion_rel else None


class ReglaFiltradoFactura(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "reglas_filtrado_factura"
    __table_args__ = {"schema": "public"}
    casilla_id = Column(BigInteger, ForeignKey("public.casillas_sat.id"), nullable=False)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text)
    criterios_json = Column(JSONB, nullable=False)
    campo_factura = Column(String(50), nullable=False)
    operacion = Column(String(20), nullable=False, default="SUMA")
    orden = Column(Integer, default=0)

    casilla = relationship("CasillaSat", back_populates="reglas_filtrado")


class ExclusionCasilla(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "exclusiones_casilla"
    __table_args__ = {"schema": "public"}
    casilla_id = Column(BigInteger, ForeignKey("public.casillas_sat.id"), nullable=False)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text)
    criterios_exclusion_json = Column(JSONB, nullable=False)

    casilla = relationship("CasillaSat", back_populates="exclusiones")


class RegimenFormularioSat(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "regimenes_formularios_sat"
    __table_args__ = (
        UniqueConstraint("regimen_id", "formulario_id", name="uq_regimen_formulario"),
        {"schema": "public"},
    )
    regimen_id = Column(BigInteger, ForeignKey("public.regimenes_fiscales.id"), nullable=False)
    formulario_id = Column(BigInteger, ForeignKey("public.formularios_sat.id"), nullable=False)
    es_obligatorio = Column(Boolean, default=True, server_default="true")

    regimen = relationship("RegimenFiscal", overlaps="formularios_sat,regimenes")
    formulario = relationship("FormularioSat", overlaps="formularios_sat,regimenes")


class MapeoCasillaCuenta(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "mapeo_casilla_cuenta"
    __table_args__ = (
        UniqueConstraint("casilla_id", "tenant_id", "empresa_id", name="uq_casilla_tenant_empresa"),
        {"schema": "public"},
    )
    casilla_id = Column(BigInteger, ForeignKey("public.casillas_sat.id"), nullable=False)
    tenant_id = Column(BigInteger, ForeignKey("public.tenants.id"), nullable=True)
    empresa_id = Column(BigInteger, nullable=True)
    codigo_cuenta_sugerido = Column(String(20), nullable=False)
    nombre_cuenta_sugerido = Column(String(255), nullable=False)
    tipo_movimiento = Column(String(10), nullable=False)

    casilla = relationship("CasillaSat", foreign_keys=[casilla_id])


# ======================================================================================
# Login Audit Tables
# ======================================================================================
class LoginAudit(BigIntPKMixin, Base):
    """Bitácora de intentos de login (exitosos y fallidos)."""

    __tablename__ = "login_audit"
    __table_args__ = {"schema": "public"}

    user_id = Column(BigInteger, ForeignKey("public.users.id", ondelete="SET NULL"), nullable=True, index=True)
    email_attempted = Column(String(255), nullable=False, index=True, comment="Email ingresado en el intento")
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(
        String(50), nullable=False, comment="SUCCESS, FAILED_INVALID_PASSWORD, FAILED_LOCKED, FAILED_USER_NOT_FOUND"
    )
    failure_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    user = relationship("User", foreign_keys=[user_id])


class PasswordResetToken(BigIntPKMixin, Base):
    """Tokens para restablecimiento de contraseña (self-service)."""

    __tablename__ = "password_reset_tokens"
    __table_args__ = {"schema": "public"}

    user_id = Column(BigInteger, ForeignKey("public.users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, unique=True, index=True, comment="Hash del token por seguridad")
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    is_used = Column(Boolean, default=False, nullable=False)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    user = relationship("User", foreign_keys=[user_id])


# =====================================================================
# Manejo de Colas de Carga de Archivos de Inventarios
# =====================================================================
class InventarioImportacionJob(BigIntPKMixin, AuditableFull, Base):
    """
    Job de importación asíncrona de inventarios.
    Tabla GLOBAL (schema public) para monitoreo centralizado.

    ⚠️ NOTA: No tiene FK estricta a inventarios_tomas porque esa tabla
    está en el schema del tenant. La integridad se maneja a nivel de aplicación.
    """

    __tablename__ = "inventarios_importacion_jobs"
    __table_args__ = (
        Index("idx_import_jobs_tenant", "tenant_id"),
        Index("idx_import_jobs_empresa", "tenant_id", "empresa_id"),
        Index("idx_import_jobs_toma", "toma_id"),
        Index("idx_import_jobs_estado", "estado"),
        Index("idx_import_jobs_usuario", "usuario_id"),
        Index("idx_import_jobs_created", "created_at"),
        {"schema": "public"},
    )

    # Identificación del tenant/empresa (sin FK, solo índice)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    empresa_id = Column(BigInteger, nullable=False, index=True)
    toma_id = Column(BigInteger, nullable=False, index=True)  # ⚠️ Sin FK
    usuario_id = Column(BigInteger, ForeignKey("public.users.id", ondelete="SET NULL"), nullable=True)

    # Archivo
    archivo_original = Column(String(255), nullable=False)
    archivo_ruta = Column(String(500), nullable=False)
    formato = Column(String(10), nullable=False)
    tamano_bytes = Column(BigInteger, nullable=False, server_default="0")
    modo = Column(String(20), nullable=False, default="REEMPLAZAR")

    # Estado del job
    estado = Column(String(20), nullable=False, default="PENDIENTE", server_default="'PENDIENTE'")
    # PENDIENTE | PROCESANDO | COMPLETADO | FALLIDO | CANCELADO | TOMA_ELIMINADA

    # Progreso
    filas_totales = Column(Integer, nullable=False, server_default="0")
    filas_procesadas = Column(Integer, nullable=False, server_default="0")
    filas_validas = Column(Integer, nullable=False, server_default="0")
    filas_con_error = Column(Integer, nullable=False, server_default="0")
    porcentaje = Column(SmallInteger, nullable=False, server_default="0")

    # Resultado (FK a tabla tenant, sin constraint estricto)
    importacion_id = Column(BigInteger, nullable=True)  # ⚠️ Sin FK
    errores = Column(JSONB)
    mensaje_error = Column(Text, nullable=True)

    # Notificación
    notificado = Column(Boolean, nullable=False, default=False, server_default="false")
    notificado_en = Column(DateTime(timezone=True), nullable=True)

    # Control de concurrencia
    iniciado_en = Column(DateTime(timezone=True), nullable=True)
    finalizado_en = Column(DateTime(timezone=True), nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<InventarioImportacionJob {self.id} - tenant={self.tenant_id} - {self.estado} ({self.porcentaje}%)>"


# =====================================================================
# Manejo de Colas de Importación FEL (Facturas Electrónicas)
# =====================================================================
class FELImportJob(BigIntPKMixin, AuditableFull, Base):
    """
    Job de importación asíncrona de facturas electrónicas (FEL).
    Tabla GLOBAL (schema public) para monitoreo centralizado.
    ⚠️ NOTA: No tiene FK estricta a facturas_electronicas porque esa tabla
     está en el schema del tenant. La integridad se maneja a nivel de aplicación.
    """

    __tablename__ = "fel_import_jobs"
    __table_args__ = (
        Index("idx_fel_jobs_tenant", "tenant_id"),
        Index("idx_fel_jobs_empresa", "tenant_id", "empresa_id"),
        Index("idx_fel_jobs_estado", "estado"),
        Index("idx_fel_jobs_usuario", "usuario_id"),
        Index("idx_fel_jobs_created", "created_at"),
        {"schema": "public"},
    )

    # Identificación del tenant/empresa (sin FK, solo índice)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    empresa_id = Column(BigInteger, nullable=False, index=True)
    usuario_id = Column(BigInteger, ForeignKey("public.users.id", ondelete="SET NULL"), nullable=True)

    # Archivo
    archivo_original = Column(String(255), nullable=False)
    archivo_ruta = Column(String(500), nullable=False)
    formato = Column(String(10), nullable=False, default="ZIP")  # ZIP
    tamano_bytes = Column(BigInteger, nullable=False, server_default="0")

    # Estado del job
    estado = Column(String(20), nullable=False, default="PENDIENTE", server_default="'PENDIENTE'")
    # PENDIENTE | PROCESANDO | COMPLETADO | FALLIDO | CANCELADO

    # Progreso
    archivos_totales = Column(Integer, nullable=False, server_default="0")
    archivos_procesados = Column(Integer, nullable=False, server_default="0")
    facturas_creadas = Column(Integer, nullable=False, server_default="0")
    facturas_duplicadas = Column(Integer, nullable=False, server_default="0")
    facturas_con_error = Column(Integer, nullable=False, server_default="0")
    porcentaje = Column(SmallInteger, nullable=False, server_default="0")

    # Resultado
    errores = Column(JSONB)
    mensaje_error = Column(Text, nullable=True)

    # Notificación
    notificado = Column(Boolean, nullable=False, default=False, server_default="false")
    notificado_en = Column(DateTime(timezone=True), nullable=True)

    # Control de concurrencia
    iniciado_en = Column(DateTime(timezone=True), nullable=True)
    finalizado_en = Column(DateTime(timezone=True), nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<FELImportJob {self.id} - tenant={self.tenant_id} - {self.estado} ({self.porcentaje}%)>"
