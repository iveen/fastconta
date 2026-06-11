# app/models/tenant_models.py
import uuid
from datetime import datetime
from decimal import Decimal

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
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from app.db.base import Base
from app.models.global_models import (
    CatalogoMoneda,
    EstadoActivoFijoEnum,
    EstadoLibro,
    RegimenFiscal,
    TipoDTE,
    TipoPersona,
)


class Empresa(Base):
    __tablename__ = "empresas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Aislamiento por Tenant
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("public.tenants.id"), nullable=False, index=True)

    # Identificación Legal y Tributaria
    nombre = Column(String(255), nullable=False)
    razon_social = Column(String(255))
    nombre_comercial = Column(String(255))
    nit = Column(String(20), unique=True, nullable=False)
    fecha_constitucion = Column(Date, nullable=True)

    # Agencia Virtual
    clave_ingreso = Column(Text, nullable=True)

    direccion = Column(Text)

    # Catalogos Globales
    regimen_fiscal_id = Column(UUID, ForeignKey('public.regimenes_fiscales.id'), nullable=True)
    tipo_persona_id = Column(UUID, ForeignKey('public.tipos_persona.id'), nullable=True)
    actividad_economica_id = Column(UUID, ForeignKey('public.actividades_economicas_sat.id'), nullable=True)

    cuenta_utilidad_periodo_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("plan_cuentas.id"), 
        nullable=True,
        comment="Cuenta de Patrimonio donde se registra el resultado del ejercicio actual"
    )

    cuenta_utilidades_acumuladas_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("plan_cuentas.id"), 
        nullable=True,
        comment="Cuenta de Patrimonio donde se acumulan los resultados de ejercicios anteriores"
    )

    # Gestión de Fechas y Estado
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relaciones (Estructura de Normalización)
    regimen_fiscal = relationship(RegimenFiscal, foreign_keys=[regimen_fiscal_id])
    tipo_persona = relationship(TipoPersona, foreign_keys=[tipo_persona_id])
    actividad_economica = relationship("ActividadEconomicaSAT", foreign_keys=[actividad_economica_id])
    

    # Relaciones 1-a-Muchos 
    representantes = relationship(
        "RepresentanteLegal", 
        back_populates="empresa", 
        cascade="all, delete-orphan"
    )

    domicilios = relationship(
        "Domicilio",
        back_populates="empresa",
        cascade="all, delete-orphan"
    )

    cuenta_utilidad_periodo = relationship(
        "CuentaContable", 
        foreign_keys=[cuenta_utilidad_periodo_id],
        lazy="select"
    )

    cuenta_utilidades_acumuladas = relationship(
        "CuentaContable", 
        foreign_keys=[cuenta_utilidades_acumuladas_id],
        lazy="select"
    )
    tenant = relationship("Tenant", back_populates="empresas")

    @property
    def domicilio_fiscal(self):
        # Helper para obtener el fiscal fácilmente
        return next((d for d in self.domicilios if d.tipo_domicilio.nombre == 'FISCAL'), None)

class Domicilio(Base):
    __tablename__ = 'domicilios'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID, ForeignKey('empresas.id'), nullable=False)
    
    # Catálogos Globales
    tipo_domicilio_id = Column(UUID, ForeignKey('public.tipos_domicilio.id'), nullable=False)
    departamento_id = Column(UUID, ForeignKey('public.departamentos.id'), nullable=False)
    municipio_id = Column(UUID, ForeignKey('public.municipios.id'), nullable=False)
    
    # Detalles específicos
    direccion_exacta = Column(String(255), nullable=False)
    zona = Column(String(10))
    codigo_postal = Column(String(10))
    
    # Relacionesse
    tipo_domicilio = relationship("TipoDomicilio")
    departamento = relationship("Departamento")
    municipio = relationship("Municipio") # Podrás acceder a municipio.departamento.nombre
    empresa = relationship("Empresa", back_populates="domicilios")

class RepresentanteLegal(Base):
    __tablename__ = 'representantes_legales'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID, ForeignKey('empresas.id'), nullable=False)
    
    nombre = Column(String(255), nullable=False)
    dpi = Column(String(20), nullable=False)
    fecha_nombramiento = Column(Date, nullable=False)
    email = Column(String(255))
    
    # Campo para control de vigencia
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    es_activo = Column(Boolean, default=True)
    
    # Relación de vuelta
    empresa = relationship("Empresa", back_populates="representantes")


#------------------- Contabilidad
class CuentaContable(Base):
    __tablename__ = "plan_cuentas"
    __table_args__ = (
        UniqueConstraint('codigo', 'empresa_id', name='plan_cuentas_codigo_empresa_unique'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(20), nullable=False, index=True)   # El índice simple lo puedes dejar o quitar
    nombre = Column(String(255), nullable=False)
    tipo = Column(String(20), nullable=False)
    naturaleza = Column(String(10), nullable=False)
    acepta_tercero = Column(Boolean, default=False)
    nivel = Column(Integer, default=1)
    cuenta_padre_id = Column(UUID(as_uuid=True), ForeignKey("plan_cuentas.id"), nullable=True)
    activa = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    empresa = relationship("Empresa", foreign_keys=[empresa_id])
    cuenta_padre = relationship(
        "CuentaContable", 
        remote_side=[id], 
        foreign_keys=[cuenta_padre_id], 
        backref="cuentas_hijas"
    )

class Partida(Base):
    __tablename__ = "partidas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # numero = Column(Integer, Sequence('partidas_numero_seq'), unique=True, nullable=False)
    numero_poliza = Column(String(50), nullable=True)
    fecha = Column(Date, nullable=False)
    descripcion = Column(Text, nullable=False)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, nullable=False)

    # Reversion
    fue_revertida = Column(Boolean, default=False)
    partida_reversion_id = Column(UUID(as_uuid=True), ForeignKey("partidas.id"), nullable=True)

    tipo_origen = Column(String(50), default='manual', nullable=False)

    empresa = relationship("Empresa")
    detalles = relationship("DetallePartida", back_populates="partida", cascade="all, delete-orphan")

class DetallePartida(Base):
    __tablename__ = "detalle_partidas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partida_id = Column(UUID(as_uuid=True), ForeignKey("partidas.id", ondelete="CASCADE"), nullable=False)
    cuenta_id = Column(UUID(as_uuid=True), ForeignKey("plan_cuentas.id"), nullable=False)
    tipo_movimiento = Column(String(10), nullable=False)  # "debe" o "haber"
    monto = Column(Numeric(12, 2), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relaciones
    partida = relationship("Partida", back_populates="detalles")
    cuenta = relationship("CuentaContable")

class Secuencia(Base):
    __tablename__ = "secuencias"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entidad = Column(String(50), nullable=False)      # ej. "partida"
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    contador = Column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint('entidad', 'empresa_id', name='uq_secuencias_entidad_empresa'),
    )

class PeriodoFiscal(Base):
    __tablename__ = "periodos_fiscales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(50), nullable=False)            # ej. "2026"
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    cerrado = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    empresa = relationship("Empresa")

#------------------ Factura Electrónica
class FacturaElectronica(Base):  # 🔹 CRÍTICO: Debe ser TenantBase, no Base
    __tablename__ = "facturas_electronicas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    xml_original = Column(Text, nullable=False)
    xml_filename = Column(String(255), nullable=True)

    numero_autorizacion = Column(String(50), nullable=False)
    autorizacion_uuid = Column(String(50), nullable=True)
    serie = Column(String(20), nullable=True)
    numero = Column(String(20), nullable=False)

    # Campos de código (para compatibilidad con frontend/legacy)
    tipo_documento = Column(String(10), nullable=True)
    moneda = Column(String(5), nullable=True)

    # 🔹 FKs simplificadas (sin "public." ni use_alter)
    tipo_documento_id = Column(
        UUID(as_uuid=True), 
        ForeignKey(TipoDTE.id), 
        nullable=True, index=True
    )
    moneda_id = Column(
        UUID(as_uuid=True), 
        ForeignKey(CatalogoMoneda.id), 
        nullable=True, index=True
    )

    fecha_emision = Column(DateTime(timezone=True), nullable=False)

    emisor_nit = Column(String(15), nullable=False)
    emisor_nombre = Column(String(255), nullable=False)
    receptor_nit = Column(String(15), nullable=False)
    receptor_nombre = Column(String(255), nullable=False)
    total_exento = Column(Numeric(12,2), default=0)
    total_gravado = Column(Numeric(12,2), default=0)
    total_iva = Column(Numeric(12,2), default=0)
    total = Column(Numeric(12,2), nullable=False)

    tipo_cambio = Column(Numeric(10, 5), nullable=True)

    es_exportacion = Column(Boolean, default=False)
    nombre_comercial = Column(String(255), nullable=True)
    tipo_operacion = Column(String(10), nullable=False, default='Compra')
    estado = Column(String(20), nullable=False, default='Activa')
    fecha_anulacion = Column(DateTime(timezone=True), nullable=True)  # Nuevo

    validado = Column(Boolean, server_default="false", default=False)
    fecha_validacion = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones estándar
    empresa = relationship("Empresa")
    detalles = relationship("FacturaDetalle", back_populates="factura", cascade="all, delete-orphan")

    # 🔹 RELACIONES EXPLÍCITAS (evita NoForeignKeysError en cross-schema)
    tipo_documento_rel = relationship(TipoDTE, lazy="select")
    moneda_rel = relationship(CatalogoMoneda, lazy="select")
    impuestos_especiales = relationship(
        "FacturaImpuestoEspecial",
        back_populates="factura",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

class FacturaImpuestoEspecial(Base):
    __tablename__ = "facturas_impuestos_especiales"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    factura_id = Column(UUID(as_uuid=True), ForeignKey("facturas_electronicas.id"), nullable=False, index=True)
    
    # ✅ NUEVO: Relación con el catálogo global (public)
    catalogo_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("public.catalogo_impuestos_especiales.id"), 
        nullable=False, 
        index=True
    )
    
    monto = Column(Numeric(12, 2), nullable=False, server_default="0")
    
    # Relación SQLAlchemy
    factura = relationship("FacturaElectronica", back_populates="impuestos_especiales")
    catalogo = relationship("CatalogoImpuestoEspecial", lazy="select") # Si quieres acceder a los datos del catálogo

class FacturaDetalle(Base):
    __tablename__ = "factura_detalles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    factura_id = Column(UUID(as_uuid=True), ForeignKey("facturas_electronicas.id", ondelete="CASCADE"), nullable=False)
    cantidad = Column(Numeric(12,4), nullable=False)
    descripcion = Column(String(500), nullable=False)
    precio_unitario = Column(Numeric(12,2), nullable=False)
    total_linea = Column(Numeric(12,2), nullable=False)
    iva_linea = Column(Numeric(12,2), default=0)
    # Relación
    factura = relationship("FacturaElectronica", back_populates="detalles")


# ------------------- Libros SAT
class SatLibro(Base):
    __tablename__ = "sat_libros"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    
    # FKs a catálogos globales (public)
    tipo_libro_id = Column(UUID(as_uuid=True), ForeignKey("public.tipos_libro.id"), nullable=False)
    regimen_fiscal_id = Column(UUID(as_uuid=True), ForeignKey("public.regimenes_fiscales.id"), nullable=False)
    estado_id = Column(UUID(as_uuid=True), ForeignKey("public.estados_libro.id"), nullable=False)
    
    # Periodo
    anio_periodo = Column(SmallInteger, nullable=False)
    mes_periodo = Column(SmallInteger, nullable=False)
    
    # Totales
    total_lineas = Column(Integer, default=0, server_default="0")
    total_exento = Column(Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    total_base_imponible = Column(Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    total_iva = Column(Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    total_monto = Column(Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    
    # Auditoría
    finalizado_por = Column(UUID(as_uuid=True), nullable=True)  
    finalizado_el = Column(DateTime(timezone=True), nullable=True)
    creado_el = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())
    
    # Relaciones
    tipo_libro = relationship("TipoLibro", foreign_keys=[tipo_libro_id])
    regimen = relationship("RegimenFiscal", foreign_keys=[regimen_fiscal_id])
    estado = relationship(EstadoLibro, foreign_keys=[estado_id])
    lineas = relationship(
        "SatLibroLinea",
        back_populates="libro",
        cascade="all, delete-orphan"
    )
    
    # Restricciones e índices
    __table_args__ = (
        CheckConstraint("mes_periodo BETWEEN 1 AND 12", name="chk_sat_libros_mes_periodo"),
        UniqueConstraint("empresa_id", "tipo_libro_id", "regimen_fiscal_id", "anio_periodo", "mes_periodo", name="uq_sat_libros_periodo"),
        Index("idx_sat_libros_empresa_periodo", "empresa_id", "anio_periodo", "mes_periodo"),
    )


class SatLibroLinea(Base):
    __tablename__ = "sat_libros_lineas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    libro_id = Column(UUID(as_uuid=True), ForeignKey("sat_libros.id", ondelete="CASCADE"), nullable=False)
    factura_id = Column(UUID(as_uuid=True), nullable=False)
    
    numero_secuencia = Column(Integer, nullable=False)
    fecha_documento = Column(Date, nullable=False)
    numero_documento = Column(String(50), nullable=False)
    nit = Column(String(20), nullable=True)
    razon_social = Column(String(255), nullable=True)
    
    es_exento = Column(Boolean, default=False, server_default="false")
    es_exonerado = Column(Boolean, default=False, server_default="false")
    
    base_imponible = Column(Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    monto_exento = Column(Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    monto_iva = Column(Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    monto_total = Column(Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    
    # Régimen Normal SAT
    credito_fiscal = Column(Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    debito_fiscal = Column(Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    
    # Relación inversa
    libro = relationship("SatLibro", back_populates="lineas")
    
    __table_args__ = (
        UniqueConstraint("libro_id", "numero_secuencia", name="uq_sat_libros_lineas_secuencia"),
        Index("idx_sat_libros_lineas_libro", "libro_id"),
    )

# ==============================================================================
# MODULO DE ACTIVOS FIJOS (Tenant Specific)
# ==============================================================================
# Asegurate de importar el enum y la categoria desde global_models al inicio de este archivo:
# from app.models.global_models import EstadoActivoFijoEnum, CategoriaActivoFijo

class ActivoFijo(Base):
    __tablename__ = "activos_fijos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False, index=True)
    
    # FK al catalogo global (esquema public). 
    # Nota: Usamos "public." explicitamente para evitar conflictos de esquema en PostgreSQL.
    categoria_id = Column(UUID(as_uuid=True), ForeignKey("categorias_activos_fijos.id"), nullable=False)
    
    # Identificacion
    codigo_interno = Column(String(50), nullable=False) # Ej: VEH-001, COMP-045
    descripcion = Column(String(255), nullable=False)
    
    # Valores y Fechas
    fecha_adquisicion = Column(Date, nullable=False)
    valor_costo = Column(Numeric(15, 2), nullable=False) # Valor de factura + impuestos no recuperables + instalacion
    valor_residual = Column(Numeric(15, 2), nullable=False, server_default="0.00") # Valor de desecho
    
    # Configuracion de depreciacion especifica para este activo
    tasa_depreciacion_anual_aplicada = Column(Numeric(5, 2), nullable=False)
    vida_util_meses_aplicada = Column(Integer, nullable=False)
    
    # Cuentas contables del tenant (Plan de Cuentas)
    # Si son NULL, el sistema debera usar las sugeridas por la categoria (a nivel de logica de negocio)
    cuenta_gasto_id = Column(UUID(as_uuid=True), ForeignKey("plan_cuentas.id"), nullable=True)
    cuenta_depreciacion_acumulada_id = Column(UUID(as_uuid=True), ForeignKey("plan_cuentas.id"), nullable=True)
    
    # Estado y Auditoria
    estado = Column(String(30), nullable=False, default=EstadoActivoFijoEnum.activo.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    empresa = relationship("Empresa")
    # Relacion con el modelo global (usamos primaryjoin si hay ambiguedad de esquema, pero con el string de FK suele bastar)
    categoria = relationship(
        "app.models.global_models.CategoriaActivoFijo",
        foreign_keys="[ActivoFijo.categoria_id]",
        lazy="select"
    ) 
    cuenta_gasto = relationship("CuentaContable", foreign_keys=[cuenta_gasto_id])
    cuenta_depreciacion_acumulada = relationship("CuentaContable", foreign_keys=[cuenta_depreciacion_acumulada_id])
    historial_depreciacion = relationship("DepreciacionActivo", back_populates="activo", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "tasa_depreciacion_anual_aplicada >= 0 AND tasa_depreciacion_anual_aplicada <= 100",
            name="chk_activos_fijos_tasa_valida"
        ),
    )


class DepreciacionActivo(Base):
    """
    Registro historico mes a mes de la depreciacion.
    Es CRITICO guardarlo para auditorias de la SAT y para no recalcular todo al vuelo.
    """
    __tablename__ = "depreciacion_activos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False, index=True)
    activo_id = Column(UUID(as_uuid=True), ForeignKey("activos_fijos.id"), nullable=False)
    
    # Periodo al que corresponde
    anio_periodo = Column(SmallInteger, nullable=False)
    mes_periodo = Column(SmallInteger, nullable=False)
    
    # Montos calculados
    monto_depreciacion_mes = Column(Numeric(15, 2), nullable=False)
    depreciacion_acumulada_hasta_fecha = Column(Numeric(15, 2), nullable=False)
    valor_en_libros = Column(Numeric(15, 2), nullable=False) # (valor_costo - depreciacion_acumulada_hasta_fecha)
    
    # Vinculo con la contabilidad del tenant
    partida_id = Column(UUID(as_uuid=True), ForeignKey("partidas.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    empresa = relationship("Empresa")
    activo = relationship("ActivoFijo", back_populates="historial_depreciacion")
    partida = relationship("Partida")

    __table_args__ = (
        UniqueConstraint("activo_id", "anio_periodo", "mes_periodo", name="uq_depreciacion_activo_periodo"),
        CheckConstraint("mes_periodo BETWEEN 1 AND 12", name="chk_depreciacion_mes_valido"),
        Index("idx_depreciacion_activos_empresa_periodo", "empresa_id", "anio_periodo", "mes_periodo"),
    )