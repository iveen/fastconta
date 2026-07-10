import enum

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
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from app.db.base import Base
from app.db.mixins import AuditableFull, BigIntPKMixin, SoftDelete


# ============================================================
# TENANT (Firma Contable) - CON SoftDelete
# ============================================================
class Tenant(BigIntPKMixin, AuditableFull, SoftDelete, Base):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "public"}

    name = Column(String(255), nullable=False)
    nit = Column(String(15), unique=True, nullable=False)
    schema_name = Column(String(63), unique=True, nullable=False)
    admin_email = Column(String(255), nullable=True)
    plan = Column(String(20), default="freemium", nullable=False)
    max_usuarios = Column(Integer, default=3, nullable=False)

    # Campos de Trial
    trial_until = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Fecha de expiración del trial (si aplica)"
    )
    trial_max_usuarios = Column(
        Integer,
        nullable=True,
        comment="Máximo de usuarios durante el trial (si aplica)"
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
    
    def get_effective_user_limit(self) -> int:
        """
        Retorna el límite efectivo de usuarios considerando el trial.
        
        Lógica:
        - Si trial_until existe Y no ha expirado → usa trial_max_usuarios
        - Si no → usa max_usuarios del plan
        
        Returns:
            int: Límite máximo de usuarios permitidos
        """
        from datetime import datetime
        
        if self.trial_until and self.trial_max_usuarios:
            now = datetime.utcnow()
            if self.trial_until > now:
                return self.trial_max_usuarios
        
        return self.max_usuarios
    
    def is_trial_active(self) -> bool:
        """Verifica si el tenant tiene un trial activo."""
        from datetime import datetime
        
        if not self.trial_until or not self.trial_max_usuarios:
            return False
        
        return self.trial_until > datetime.utcnow()
    
    def trial_days_remaining(self) -> int | None:
        """Retorna los días restantes del trial, o None si no hay trial activo."""
        from datetime import datetime
        
        if not self.is_trial_active():
            return None
        
        delta = self.trial_until - datetime.utcnow()
        return max(0, delta.days)

class RegistrationAttempt(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "registration_attempts"
    __table_args__ = {"schema": "public"}
    ip_address = Column(String(45), nullable=False)

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
    __table_args__ = {'schema': 'public'}
    codigo = Column(String(10), unique=True, nullable=False, index=True)
    descripcion = Column(String(100), nullable=False)
    requiere_complemento = Column(Boolean, default=False, nullable=False)
    es_factura = Column(Boolean, default=True, nullable=False)


class CatalogoMoneda(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "catalogo_monedas"
    __table_args__ = {'schema': 'public'}
    codigo_banguat = Column(String(5), unique=True, nullable=False, index=True)
    codigo_iso = Column(String(3), unique=True, nullable=False, index=True)
    nombre = Column(String(50), nullable=False)
    simbolo = Column(String(5), nullable=True)
    decimales = Column(Integer, default=2, nullable=False)


class CatalogoImpuestoEspecial(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "catalogo_impuestos_especiales"
    __table_args__ = {'schema': 'public'}
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
    __tablename__ = 'tipos_persona'
    __table_args__ = {'schema': 'public'}
    nombre = Column(String(50), nullable=False, unique=True)
    descripcion = Column(String(200), nullable=True)


class TipoDomicilio(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = 'tipos_domicilio'
    __table_args__ = {'schema': 'public'}
    nombre = Column(String(50), nullable=False, unique=True)


class Departamento(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = 'departamentos'
    __table_args__ = {'schema': 'public'}
    codigo_iso = Column(String(2), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    municipios = relationship("Municipio", back_populates="departamento")


class Municipio(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = 'municipios'
    __table_args__ = {'schema': 'public'}
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
        Boolean, default=True, nullable=False,
        comment="Indica si el usuario debe cambiar su contraseña en el próximo login"
    )
    password_changed_at = Column(
        DateTime(timezone=True), nullable=True,
        comment="Fecha del último cambio de contraseña"
    )
    password_expires_at = Column(
        DateTime(timezone=True), nullable=True,
        comment="Fecha de expiración de la contraseña (90 días)"
    )
    
    # ✅ NUEVO: Política de bloqueo por intentos fallidos
    failed_login_attempts = Column(
        Integer, default=0, nullable=False,
        comment="Contador de intentos fallidos consecutivos"
    )
    locked_until = Column(
        DateTime(timezone=True), nullable=True,
        comment="Fecha hasta la cual el usuario está bloqueado"
    )
    is_locked = Column(
        Boolean, default=False, nullable=False,
        comment="Indica si el usuario está bloqueado (por intentos fallidos o admin)"
    )
    
    tenant = relationship("Tenant", back_populates="users", foreign_keys=[tenant_id])
    role = relationship("Role", foreign_keys=[role_id], lazy="selectin")
    empresas_asignadas = relationship(
        "UserEmpresa", back_populates="user",
        foreign_keys="[UserEmpresa.user_id]",
        cascade="all, delete-orphan"
    )

class UserEmpresa(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "user_empresas"
    __table_args__ = (
        UniqueConstraint('user_id', 'tenant_id', 'empresa_id', name='uq_user_empresa_tenant'),
        {"schema": "public"}
    )
    user_id = Column(
        BigInteger,
        ForeignKey("public.users.id", ondelete="CASCADE"),
        nullable=False
    )
    tenant_id = Column(
        BigInteger,
        ForeignKey("public.tenants.id", ondelete="CASCADE"),
        nullable=False
    )
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
        {"schema": "public"}
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
        "RegimenImpuestoConfig", 
        back_populates="regimen", 
        cascade="all, delete-orphan"
    )
    formularios_sat = relationship(
        "FormularioSat",
        secondary="public.regimenes_formularios_sat",
        back_populates="regimenes"
    )


class CatalogoImpuesto(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "catalogo_impuestos"
    __table_args__ = {"schema": "public"}
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=False)
    tasa_porcentaje = Column(Numeric(5, 2), nullable=True)
    tasa_fija_monto = Column(Numeric(15, 2), nullable=True, server_default='0.00')
    limite_inferior = Column(Numeric(15, 2), nullable=True, server_default='0.00')
    limite_superior = Column(Numeric(15, 2), nullable=True)
    frecuencia_pago = Column(String(20), nullable=False)
    frecuencia_liquidacion = Column(String(20), nullable=False)
    es_acreditable = Column(Boolean, default=False, nullable=False)
    requiere_autorizacion_sat = Column(Boolean, default=False, nullable=False)


class RegimenImpuestoConfig(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "regimen_impuesto_config"
    __table_args__ = (
        UniqueConstraint('regimen_id', 'impuesto_id', name='uq_regimen_impuesto_unico'),
        {"schema": "public"},
    )
    regimen_id = Column(BigInteger, ForeignKey("public.regimenes_fiscales.id"), nullable=False, index=True)
    impuesto_id = Column(BigInteger, ForeignKey("public.catalogo_impuestos.id"), nullable=False, index=True)
    
    tasa_porcentaje = Column(Numeric(5, 2), nullable=True)
    tasa_fija_monto = Column(Numeric(15, 2), nullable=True, server_default='0.00')
    limite_inferior = Column(Numeric(15, 2), nullable=True, server_default='0.00')
    limite_superior = Column(Numeric(15, 2), nullable=True)
    es_acreditable = Column(Boolean, default=False, nullable=False)
    es_retencion_definitiva = Column(Boolean, default=False, nullable=False)
    requiere_autorizacion_sat = Column(Boolean, default=False, nullable=False)

    regimen = relationship("RegimenFiscal", back_populates="configuraciones_impuestos")
    impuesto = relationship("CatalogoImpuesto")


class RegimenDteConfig(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = 'regimen_dte_config'
    __table_args__ = {'schema': 'public'}
    regimen_id = Column(BigInteger, ForeignKey('public.regimenes_fiscales.id'), nullable=False)
    dte_id = Column(BigInteger, ForeignKey('public.tipos_dte.id'), nullable=False)
    es_exclusivo = Column(Boolean, default=False, nullable=False)

    regimen = relationship("RegimenFiscal")
    dte = relationship("TipoDTE")


# ============================================================
# FORMULARIOS SAT - CON SoftDelete
# ============================================================
class FormularioSat(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "formularios_sat"
    __table_args__ = (
        UniqueConstraint('codigo', 'version', name='uq_formulario_codigo_version'),
        Index('idx_formularios_vigencia', 'codigo', 'fecha_vigencia_desde', 'fecha_vigencia_hasta'),
        {"schema": "public"}
    )
    codigo = Column(String(20), nullable=False, index=True)
    version = Column(String(10), nullable=False, default='1.0')
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text)
    fecha_vigencia_desde = Column(Date, nullable=False, server_default=text("CURRENT_DATE"))
    fecha_vigencia_hasta = Column(Date, nullable=True)
    es_version_activa = Column(Boolean, default=True, server_default="true")
    editable = Column(Boolean, default=True, server_default="true", nullable=False)
    formulario_padre_id = Column(BigInteger, ForeignKey("public.formularios_sat.id"), nullable=True)
    
    secciones = relationship("SeccionFormulario", back_populates="formulario", cascade="all, delete-orphan")
    regimenes = relationship(
        "RegimenFiscal",
        secondary="public.regimenes_formularios_sat",
        back_populates="formularios_sat"
    )
    version_hija = relationship(
        "FormularioSat",
        back_populates="version_padre",
        foreign_keys=[formulario_padre_id],
        remote_side=[formulario_padre_id]
    )
    # ✅ CORREGIDO: Usar string en lugar de referencia directa
    version_padre = relationship(
        "FormularioSat",
        back_populates="version_hija",
        foreign_keys=[formulario_padre_id],
        remote_side="FormularioSat.id"  # ✅ String en lugar de [id]
    )
    
    @property
    def nombre_completo(self):
        return f"{self.codigo} v{self.version}"
    

class SeccionFormulario(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "secciones_formulario"
    __table_args__ = (
        UniqueConstraint('formulario_id', 'numero_seccion', name='uq_seccion_formulario'),
        {"schema": "public"}
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
    __table_args__ = (
        UniqueConstraint('seccion_id', 'codigo', name='uq_casilla_seccion_codigo'),
        {"schema": "public"}
    )
    seccion_id = Column(BigInteger, ForeignKey("public.secciones_formulario.id"), nullable=True)
    codigo = Column(String(50), nullable=False)
    codigo_visual = Column(String(20), nullable=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text)
    orden_seccion = Column(Integer, default=0)
    tipo_casilla = Column(String(30), nullable=False, default='CALCULO')
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
    operacion = Column(String(20), nullable=False, default='SUMA')
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
        UniqueConstraint('regimen_id', 'formulario_id', name='uq_regimen_formulario'),
        {"schema": "public"}
    )
    regimen_id = Column(BigInteger, ForeignKey("public.regimenes_fiscales.id"), nullable=False)
    formulario_id = Column(BigInteger, ForeignKey("public.formularios_sat.id"), nullable=False)
    es_obligatorio = Column(Boolean, default=True, server_default="true")

    regimen = relationship("RegimenFiscal", overlaps="formularios_sat,regimenes")
    formulario = relationship("FormularioSat", overlaps="formularios_sat,regimenes")


class MapeoCasillaCuenta(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = "mapeo_casilla_cuenta"
    __table_args__ = (
        UniqueConstraint('casilla_id', 'tenant_id', 'empresa_id', name='uq_casilla_tenant_empresa'),
        {"schema": "public"}
    )
    casilla_id = Column(BigInteger, ForeignKey("public.casillas_sat.id"), nullable=False)
    tenant_id = Column(BigInteger, ForeignKey("public.tenants.id"), nullable=True)
    empresa_id = Column(BigInteger, nullable=True)
    codigo_cuenta_sugerido = Column(String(20), nullable=False)
    nombre_cuenta_sugerido = Column(String(255), nullable=False)
    tipo_movimiento = Column(String(10), nullable=False)

    casilla = relationship("CasillaSat", foreign_keys=[casilla_id])
    tenant = relationship("Tenant", foreign_keys=[tenant_id])