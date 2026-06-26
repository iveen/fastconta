import enum
import uuid

from sqlalchemy import (
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
from sqlalchemy.dialects.postgresql import JSON, JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from app.db.base import Base
from app.db.mixins import AuditableFull


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
    codigo_prefijo = Column(String(10), nullable=False, unique=True, index=True, comment="Prefijo para código interno (ej: VEH, COMP)")
    
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
    # Dentro de class RegimenFiscal(Base):
    formularios_sat = relationship(
        "FormularioSat",
        secondary="public.regimenes_formularios_sat",
        back_populates="regimenes"
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

#------------------------------------------------------
# Catálogos Declaraciones SAT
#------------------------------------------------------
class FormularioSat(AuditableFull, Base):
    """
    Catálogo global de formularios de la SAT (2237, 2046, 2276, 1031, etc.)
    SOPORTA VERSIONADO: Permite mantener múltiples versiones del mismo formulario
    """
    __tablename__ = "formularios_sat"
    __table_args__ = (
        UniqueConstraint('codigo', 'version', name='uq_formulario_codigo_version'),
        Index('idx_formularios_vigencia', 'codigo', 'fecha_vigencia_desde', 'fecha_vigencia_hasta'),
        {"schema": "public"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(20), nullable=False, index=True)  # Ej: 'SAT-2237' (sin unique)
    version = Column(String(10), nullable=False, default='1.0')  # Ej: '1.0', '2.0'
    
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text)
    
    # Versionado y Vigencia
    fecha_vigencia_desde = Column(Date, nullable=False, server_default=text("CURRENT_DATE"))
    fecha_vigencia_hasta = Column(Date, nullable=True)  # NULL = vigente actualmente
    es_version_activa = Column(Boolean, default=True, server_default="true")
    
    editable = Column(Boolean, default=True, server_default="true", nullable=False)
    
    # Auto-referencia para versionado
    formulario_padre_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("public.formularios_sat.id"), 
        nullable=True,
        comment="ID del formulario versión anterior (para duplicación)"
    )
    
    # Relaciones
    #============================================================================
    # La relación uno a muchos de Formulario a Casillas fue eliminada
    # por cambios en el diseño, y la creación de una tabla Sección
    # que contendrá casillas, mientras el formulario contendrá Secciones
    #============================================================================
    # casillas = relationship("CasillaSat", back_populates="formulario", cascade="all, delete-orphan")
    #============================================================================
    secciones = relationship("SeccionFormulario", back_populates="formulario", cascade="all, delete-orphan")
    
    # Relación N:M con Regimenes
    regimenes = relationship(
        "RegimenFiscal",
        secondary="public.regimenes_formularios_sat",
        back_populates="formularios_sat"
    )
    
    # Auto-relación para versionado
    version_hija = relationship(
        "FormularioSat",
        back_populates="version_padre",
        foreign_keys=[formulario_padre_id],
        remote_side=[formulario_padre_id]
    )

    version_padre = relationship(
        "FormularioSat",
        back_populates="version_hija",
        foreign_keys=[formulario_padre_id],
        remote_side=[id]
    )
    
    @property
    def nombre_completo(self):
        return f"{self.codigo} v{self.version}"

class CasillaSat(AuditableFull, Base):
    """
    Catálogo global de cada fila/casilla de los formularios SAT.
    Cada versión de formulario tiene sus propias casillas.
    """
    __tablename__ = "casillas_sat"
    __table_args__ = (
        UniqueConstraint('seccion_id', 'codigo', name='uq_casilla_seccion_codigo'),
        {"schema": "public"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    #============================================================================
    # formulario_id ha sido eliminado al no ser necesario
    # por cambios en el diseño, y la creación de una tabla Sección
    # que contendrá casillas, mientras el formulario contendrá Secciones
    #============================================================================
    # formulario_id = Column(UUID(as_uuid=True), ForeignKey("public.formularios_sat.id"), nullable=False)
    #============================================================================
    seccion_id = Column(UUID(as_uuid=True), ForeignKey("public.secciones_formulario.id"), nullable=True)

    
    # Identificación
    codigo = Column(String(50), nullable=False)  # Ej: '3.1', '4.2' (no unique global)
    codigo_visual = Column(String(20), nullable=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text)
    
    # Ubicación
    @property
    def seccion(self) -> str | None:
        """Retorna el número de sección al que pertenece esta casilla"""
        if self.seccion_rel:  # Asumiendo que la relación se llama seccion_rel
            return self.seccion_rel.numero_seccion
        return None
    orden_seccion = Column(Integer, default=0)
    
    # Configuración
    tipo_casilla = Column(String(30), nullable=False, default='CALCULO')
    naturaleza = Column(String(20), nullable=True)
    formula_calculo = Column(Text, nullable=True)
    porcentaje_aplicable = Column(Numeric(5, 2), nullable=True)
    campo_origen_factura = Column(String(50), nullable=True)
    
    # Banderas
    es_editable = Column(Boolean, default=False, server_default="false")
    requiere_justificacion = Column(Boolean, default=False, server_default="false")
    es_visible_usuario = Column(Boolean, default=True, server_default="true")
    es_automatica = Column(Boolean, nullable=False, default=False, server_default="false")

    dependencias = Column(
        JSON, nullable=True,
        comment="Lista de códigos de casillas de las que depende ['3.1','3.2']"
    )

    funcion_calculo = Column(
        String(50), nullable=True,
        comment="Nombre de funcion especializada: 'isr_progresivo', 'max_cero', etc."
    )

    parametros_funcion = Column(
        JSON, nullable=True,
        comment="Parámetros: {'tramos': [{'hasta': 30000, 'tasa': 0.05}, ...]}"
    )
    
    # Relaciones
    seccion_rel = relationship("SeccionFormulario", back_populates="casillas")
    reglas_filtrado = relationship("ReglaFiltradoFactura", back_populates="casilla", cascade="all, delete-orphan")
    exclusiones = relationship("ExclusionCasilla", back_populates="casilla", cascade="all, delete-orphan")
    detalles = relationship("DetalleDeclaracionImpuesto", back_populates="casilla")
    
    # ✅ Propiedad para obtener formulario_id vía seccion
    @property
    def formulario_id(self):
        return self.seccion_rel.formulario_id if self.seccion_rel else None

class RegimenFormularioSat(AuditableFull, Base):
    """
    TABLA PUENTE: Define qué formularios debe presentar cada régimen fiscal.
    Esto permite que el sistema sepa automáticamente qué declaraciones 
    generar al seleccionar una empresa.
    """
    __tablename__ = "regimenes_formularios_sat"
    __table_args__ = (
        UniqueConstraint('regimen_id', 'formulario_id', name='uq_regimen_formulario'),
        {"schema": "public"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    regimen_id = Column(UUID(as_uuid=True), ForeignKey("public.regimenes_fiscales.id"), nullable=False)
    formulario_id = Column(UUID(as_uuid=True), ForeignKey("public.formularios_sat.id"), nullable=False)
    
    # Banderas de control
    es_obligatorio = Column(Boolean, default=True, server_default="true")
    # Ej: El SAT-2237 es obligatorio para RG, pero el SAT-1031 es anual.
    # El frontend puede usar esto para filtrar qué mostrar en el dashboard mensual.
    
    # Relaciones
    regimen = relationship("RegimenFiscal", overlaps="formularios_sat,regimenes")
    formulario = relationship("FormularioSat", overlaps="formularios_sat,regimenes")

# =============================================================
# REDISEÑO: Configuración Avanzada de Formularios SAT
# Permite configurar dinámicamente cualquier formulario SAT
# sin tocar código (solo datos). Soporta fórmulas, filtros,
# exclusiones (ej: FYDUCA Honduras) y mapeo contable.
# =============================================================

class SeccionFormulario(AuditableFull, Base):
    """
    Representa una sección lógica del formulario SAT.
    Ejemplo: "Sección 3: Débito Fiscal por Operaciones Locales"
    
    Esto permite:
    - Agrupar casillas visualmente
    - Aplicar lógica de negocio por sección
    - Reordenar secciones sin tocar código
    """
    __tablename__ = "secciones_formulario"
    __table_args__ = (
        UniqueConstraint('formulario_id', 'numero_seccion', name='uq_seccion_formulario'),
        {"schema": "public"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    formulario_id = Column(UUID(as_uuid=True), ForeignKey("public.formularios_sat.id"), nullable=False)
    
    # Identificación
    numero_seccion = Column(String(10), nullable=False)  # '3', '4', '5', '7'
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text)
    orden = Column(Integer, nullable=False, default=0)
    
    # Tipo de sección para lógica de negocio
    tipo_seccion = Column(String(30), nullable=False)
    # Valores: 'IDENTIFICACION', 'PERIODO', 'DEBITO_FISCAL', 'CREDITO_FISCAL',
    #          'EXPORTACIONES', 'DETERMINACION', 'INFORMATIVA', 'DOCUMENTOS'
    
    # Banderas de control
    es_obligatoria = Column(Boolean, default=True, server_default="true")
    requiere_exportador = Column(Boolean, default=False, server_default="false")
    es_automatica = Column(Boolean, default=False, nullable=False, server_default="false")
    
    # Relaciones
    formulario = relationship("FormularioSat", back_populates="secciones")
    casillas = relationship("CasillaSat", back_populates="seccion_rel", cascade="all, delete-orphan")


class ReglaFiltradoFactura(AuditableFull, Base):
    """
    Define qué facturas alimentan una casilla específica.
    
    Ejemplo: "Casilla 3.2 solo recibe facturas de tipo 'Venta',
    que NO sean exentas, y que NO sean exportaciones."
    
    Los criterios se guardan como JSON para máxima flexibilidad:
    {"tipo_operacion": "Venta", "es_exento": false, "es_exportacion": false}
    """
    __tablename__ = "reglas_filtrado_factura"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    casilla_id = Column(UUID(as_uuid=True), ForeignKey("public.casillas_sat.id"), nullable=False)
    
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text)
    
    # Criterios de filtrado en JSON
    criterios_json = Column(JSONB, nullable=False)
    
    # Campo de la factura a sumar
    campo_factura = Column(String(50), nullable=False)  # 'total_gravado_gtq', 'total_iva_gtq'
    
    operacion = Column(String(20), nullable=False, default='SUMA')  # SUMA, COUNT, PROMEDIO
    orden = Column(Integer, default=0)
    es_activa = Column(Boolean, default=True, server_default="true")
    
    # Relaciones
    casilla = relationship("CasillaSat", back_populates="reglas_filtrado")


class ExclusionCasilla(AuditableFull, Base):
    """
    Define exclusiones específicas para una casilla.
    
    Caso de uso crítico: FYDUCA Honduras debe ir en casilla separada
    de "Exportaciones Centroamérica", así que excluimos de 4.1.
    
    Criterios en JSON:
    {"tipo_documento": "FYDUCA", "pais_destino": "HND"}
    """
    __tablename__ = "exclusiones_casilla"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    casilla_id = Column(UUID(as_uuid=True), ForeignKey("public.casillas_sat.id"), nullable=False)
    
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text)
    
    # Criterios de exclusión en JSON
    criterios_exclusion_json = Column(JSONB, nullable=False)
    
    es_activa = Column(Boolean, default=True, server_default="true")
    
    # Relaciones
    casilla = relationship("CasillaSat", back_populates="exclusiones")


class MapeoCasillaCuenta(AuditableFull, Base):
    """
    Mapea casillas SAT a cuentas contables del tenant.
    
    Permite que al cerrar una declaración se generen
    partidas contables automáticas.
    
    Puede ser global (tenant_id NULL) o específico por tenant.
    """
    __tablename__ = "mapeo_casilla_cuenta"
    __table_args__ = (
        UniqueConstraint('casilla_id', 'tenant_id', 'empresa_id', name='uq_casilla_tenant_empresa'),
        {"schema": "public"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    casilla_id = Column(UUID(as_uuid=True), ForeignKey("public.casillas_sat.id"), nullable=False)
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("public.tenants.id"), nullable=True)
    empresa_id = Column(UUID(as_uuid=True), nullable=True)
    
    codigo_cuenta_sugerido = Column(String(20), nullable=False)
    nombre_cuenta_sugerido = Column(String(255), nullable=False)
    tipo_movimiento = Column(String(10), nullable=False)  # 'DEBE', 'HABER'
    
    # Relaciones
    casilla = relationship("CasillaSat")
    tenant = relationship("Tenant")