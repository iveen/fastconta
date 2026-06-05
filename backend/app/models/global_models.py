import enum
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 1. Datos de Identidad de la Firma
    name = Column(String(255), nullable=False)
    nit = Column(String(15), unique=True, nullable=False)       # NIT de la firma contable
    schema_name = Column(String(63), unique=True, nullable=False) # Ej: tenant_firma_x
    
    # 3. Configuración Comercial (Planes y Límites)
    admin_email = Column(String(255), nullable=True)
    plan = Column(String(20), default="freemium", nullable=False)
    max_empresas = Column(Integer, default=5, nullable=False)     # Límite de empresas clientes
    max_usuarios = Column(Integer, default=3, nullable=False)     # Límite de contadores en la firma
    
    # 4. Estado
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    users = relationship("User", back_populates="tenant")
    empresas = relationship("Empresa", back_populates="tenant", cascade="all, delete-orphan")

class RegistrationAttempt(Base):
    __tablename__ = "registration_attempts"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_address = Column(String(45), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TipoDTE(Base):
    __tablename__ = "tipos_dte"
    __table_args__ = {'schema': 'public'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(10), unique=True, nullable=False, index=True)
    descripcion = Column(String(100), nullable=False)
    requiere_complemento = Column(Boolean, default=False, nullable=False)
    es_factura = Column(Boolean, default=True, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class CatalogoMoneda(Base):
    __tablename__ = "catalogo_monedas"
    __table_args__ = {'schema': 'public'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo_banguat = Column(String(5), unique=True, nullable=False, index=True)
    codigo_iso = Column(String(3), unique=True, nullable=False, index=True)
    nombre = Column(String(50), nullable=False)
    simbolo = Column(String(5), nullable=True)
    decimales = Column(Integer, default=2, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class CatalogoImpuestoEspecial(Base):
    __tablename__ = "catalogo_impuestos_especiales"
    __table_args__ = {'schema': 'public'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(50), unique=True, nullable=False, index=True)  # ej: 'petroleo'
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

class TipoLibro(Base):
    __tablename__ = "tipos_libro"
    __table_args__ = {"schema": "public"} # <--- Clave
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(50), nullable=False)
    nombre = Column(String(255), nullable=False, unique=True)

class EstadoLibro(Base):
    __tablename__ = "estados_libro"
    __table_args__ = {"schema": "public"}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(50), nullable=False)

class RegimenDteConfig(Base):
    __tablename__ = 'regimen_dte_config'
    __table_args__ = {'schema': 'public'}

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    regimen_id = Column(UUID, ForeignKey('public.regimenes_fiscales.id'), nullable=False)
    dte_id = Column(UUID, ForeignKey('public.tipos_dte.id'), nullable=False)
    es_exclusivo = Column(Boolean, default=False, nullable=False)

    # Relaciones para facilidad de acceso
    regimen = relationship("RegimenFiscal") 
    dte = relationship("TipoDTE")


class TipoPersona(Base):
    __tablename__ = 'tipos_persona'
    __table_args__ = {'schema': 'public'}
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    nombre = Column(String(50), nullable=False) # NATURAL, JURIDICA, etc.
    
class TipoDomicilio(Base):
    __tablename__ = 'tipos_domicilio'
    __table_args__ = {'schema': 'public'}
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    nombre = Column(String(50), nullable=False, unique=True) # "Fiscal", "Operativo", "Sucursal"

class Departamento(Base):
    __tablename__ = 'departamentos'
    __table_args__ = {'schema': 'public'}
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    codigo_iso = Column(String(2), nullable=False)
    nombre = Column(String(100))
    municipios = relationship("Municipio", back_populates="departamento")

class Municipio(Base):
    __tablename__ = 'municipios'
    __table_args__ = {'schema': 'public'}
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    codigo_iso = Column(String(4), nullable=False)
    nombre = Column(String(100), nullable=False)
    departamento_id = Column(UUID, ForeignKey("public.departamentos.id"), nullable=False)
    departamento = relationship("Departamento", back_populates="municipios")

class ActividadEconomicaSAT(Base):
    __tablename__ = "actividades_economicas_sat"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo_sat = Column(String(20), unique=True, nullable=False, index=True)
    nombre_actividad = Column(String(255), nullable=False)
    seccion = Column(String(255), nullable=True)
    activa = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ---- RBAC
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # ✅ tenant_id ahora es NULLABLE para permitir superadmin sin tenant
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("public.tenants.id"), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    
    # ✅ FK al catálogo de roles en lugar de String plano
    role_id = Column(UUID(as_uuid=True), ForeignKey("public.roles.id"), nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    tenant = relationship("Tenant", back_populates="users")
    role = relationship("Role", lazy="selectin")
    empresas_asignadas = relationship("UserEmpresa", back_populates="user", cascade="all, delete-orphan")

    tenant = relationship("Tenant", back_populates="users")

class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(30), unique=True, nullable=False, index=True)  # 'superadmin', 'tenant_manager', 'tenant_member', 'tenant_client'
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    nivel_acceso = Column(Integer, nullable=False)  # 100=global, 80=tenant_admin, 60=miembro_restringido, 20=cliente_solo_lectura

class UserEmpresa(Base):
    __tablename__ = "user_empresas"
    __table_args__ = (
        UniqueConstraint('user_id', 'tenant_id', 'empresa_id', name='uq_user_empresa_tenant'),
        {"schema": "public"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("public.users.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("public.tenants.id", ondelete="CASCADE"), nullable=False)
    
    # 👇 Sin ForeignKey: validación se hace en capa de aplicación
    empresa_id = Column(UUID(as_uuid=True), nullable=False)
    
    activo = Column(Boolean, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    tenant = relationship("Tenant")

class EstadoActivoFijoEnum(str, enum.Enum):
    activo = "activo"
    totalmente_depreciado = "totalmente_depreciado"
    dado_baja = "dado_baja"
    vendido = "vendido"

class CategoriaActivoFijo(Base):
    __tablename__ = "categorias_activos_fijos"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Nombre del tipo de activo (Ej: "Vehiculos", "Equipo de Computo", "Edificios")
    nombre = Column(String(100), nullable=False, unique=True)

    # ✅ NUEVO CAMPO: Descripción legal basada en la Ley de ISR / Decreto 10-2012
    descripcion = Column(Text, nullable=True) 
    
    # Porcentajes anuales segun limites de la SAT (Decreto 10-2012 y AG 142-2013)
    # Se almacenan como decimales (Ej: 20.00 para 20%)
    tasa_minima_anual = Column(Numeric(5, 2), nullable=False, server_default="0.00")
    tasa_maxima_anual = Column(Numeric(5, 2), nullable=False)
    vida_util_meses_default = Column(Integer, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint("tasa_maxima_anual >= tasa_minima_anual", name="chk_categoria_tasa_valida"),
    )

#------------------------------------------------------
# Catálogos Motor Tributario
#------------------------------------------------------

class RegimenFiscal(Base):
    __tablename__ = "regimenes_fiscales"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(50), unique=True, nullable=False, index=True) # Ej: 'PC_FEL', 'RG_UTILIDADES', 'ROS'
    nombre = Column(String(100), nullable=False) # Ej: 'Pequeno Contribuyente Electronico (FEL)'
    descripcion = Column(Text, nullable=True) # Ej: 'Art. 45 Dec. 10-2012. 4% mensual. No genera credito fiscal.'
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relacion con la tabla puente
    configuraciones_impuestos = relationship(
        "RegimenImpuestoConfig", 
        back_populates="regimen", 
        cascade="all, delete-orphan"
    )


class CatalogoImpuesto(Base):
    __tablename__ = "catalogo_impuestos"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identificacion
    codigo = Column(String(20), unique=True, nullable=False, index=True) # Ej: 'IVA', 'ISR_RG', 'ISR_ROS_1', 'ISO'
    nombre = Column(String(100), nullable=False) # Ej: 'Impuesto sobre la Renta - Regimen General'
    descripcion = Column(Text, nullable=False) # Ej: 'Art. 36 Ley 26-92. 25% sobre utilidades netas. Pagos trimestrales.'
    
    # Parametros de Calculo (Soporta tramos progresivos)
    tasa_porcentaje = Column(Numeric(5, 2), nullable=True) # Ej: 25.00, 5.00, 1.00 (NULL si es monto fijo puro)
    tasa_fija_monto = Column(Numeric(15, 2), nullable=True, server_default='0.00') # Ej: 1500.00 (para ROS > 30k)
    
    # Limites del tramo (Para impuestos progresivos como el ROS)
    limite_inferior = Column(Numeric(15, 2), nullable=True, server_default='0.00') # Ej: 30000.01
    limite_superior = Column(Numeric(15, 2), nullable=True) # Ej: NULL (infinito)
    
    # Frecuencias y Reglas Fiscales
    frecuencia_pago = Column(String(20), nullable=False) # 'MENSUAL', 'TRIMESTRAL', 'ANUAL'
    frecuencia_liquidacion = Column(String(20), nullable=False) # 'MENSUAL', 'TRIMESTRAL', 'ANUAL'
    
    # Reglas Especiales SAT
    es_acreditable = Column(Boolean, default=False, nullable=False) # Ej: True para ISO (acreditable contra ISR)
    requiere_autorizacion_sat = Column(Boolean, default=False, nullable=False) # Ej: True para ROS pago directo
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RegimenImpuestoConfig(Base):
    __tablename__ = "regimen_impuesto_config"
    __table_args__ = (
        # Un regimen solo puede tener UNA configuracion por tipo de impuesto
        UniqueConstraint('regimen_id', 'impuesto_id', name='uq_regimen_impuesto_unico'),
        {"schema": "public"},
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Llaves foraneas
    regimen_id = Column(UUID(as_uuid=True), ForeignKey("public.regimenes_fiscales.id"), nullable=False, index=True)
    impuesto_id = Column(UUID(as_uuid=True), ForeignKey("public.catalogo_impuestos.id"), nullable=False, index=True)
    
    # Parametros de calculo ESPECIFICOS para esta combinacion Regimen + Impuesto
    # (Si son NULL, el sistema puede heredar los valores base del CatalogoImpuesto)
    tasa_porcentaje = Column(Numeric(5, 2), nullable=True) # Ej: 4.00 para PC FEL, 25.00 para RG
    tasa_fija_monto = Column(Numeric(15, 2), nullable=True, server_default='0.00') # Ej: 1500.00 para ROS > 30k
    
    limite_inferior = Column(Numeric(15, 2), nullable=True, server_default='0.00') # Ej: 30000.01
    limite_superior = Column(Numeric(15, 2), nullable=True) # Ej: 300000.00 (Limite anual PC)
    
    # Banderas de comportamiento fiscal (CRITICAS para la logica de negocio)
    es_acreditable = Column(Boolean, default=False, nullable=False) # ¿Genera credito fiscal para el comprador? (Falso para PC)
    es_retencion_definitiva = Column(Boolean, default=False, nullable=False) # ¿El pago es definitivo? (Verdadero para PC)
    requiere_autorizacion_sat = Column(Boolean, default=False, nullable=False) # Ej: ROS con pago directo
    
    # Relaciones
    regimen = relationship("RegimenFiscal", back_populates="configuraciones_impuestos")
    impuesto = relationship("CatalogoImpuesto")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())