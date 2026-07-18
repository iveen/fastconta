# app/models/tenant_models.py
from decimal import Decimal

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
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.db.mixins import AuditableFull, BigIntPKMixin, SoftDelete
from app.models.global_models import (
    CatalogoMoneda,
    EstadoActivoFijoEnum,
    EstadoLibro,
    RegimenFiscal,
    TipoDTE,
    TipoPersona,
)


# ============================================================
# EMPRESA - CON SoftDelete
# ============================================================
class Empresa(AuditableFull, BigIntPKMixin, SoftDelete, Base):
    __tablename__ = "empresas"
    
    tenant_id = Column(BigInteger, ForeignKey("public.tenants.id"), nullable=False, index=True)
    nombre = Column(String(255), nullable=False)
    razon_social = Column(String(255))
    nombre_comercial = Column(String(255))
    nit = Column(String(20), unique=True, nullable=False)
    fecha_constitucion = Column(Date, nullable=True)
    clave_ingreso = Column(Text, nullable=True)
    direccion = Column(Text)

    regimen_fiscal_id = Column(BigInteger, ForeignKey('public.regimenes_fiscales.id'), nullable=True)
    tipo_persona_id = Column(BigInteger, ForeignKey('public.tipos_persona.id'), nullable=True)
    actividad_economica_id = Column(BigInteger, ForeignKey('public.actividades_economicas_sat.id'), nullable=True)
    cuenta_utilidad_periodo_id = Column(BigInteger, ForeignKey("plan_cuentas.id"), nullable=True)
    cuenta_utilidades_acumuladas_id = Column(BigInteger, ForeignKey("plan_cuentas.id"), nullable=True)

    regimen_fiscal = relationship(RegimenFiscal, foreign_keys=[regimen_fiscal_id])
    tipo_persona = relationship(TipoPersona, foreign_keys=[tipo_persona_id])
    actividad_economica = relationship("ActividadEconomicaSAT", foreign_keys=[actividad_economica_id])
    representantes = relationship("RepresentanteLegal", back_populates="empresa", cascade="all, delete-orphan")
    domicilios = relationship("Domicilio", back_populates="empresa", cascade="all, delete-orphan")
    cuenta_utilidad_periodo = relationship("CuentaContable", foreign_keys=[cuenta_utilidad_periodo_id], lazy="select")
    cuenta_utilidades_acumuladas = relationship("CuentaContable", foreign_keys=[cuenta_utilidades_acumuladas_id], lazy="select")
    tenant = relationship("Tenant", back_populates="empresas")

    @property
    def domicilio_fiscal(self):
        return next((d for d in self.domicilios if d.tipo_domicilio.nombre == 'FISCAL'), None)


class Domicilio(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = 'domicilios'
    empresa_id = Column(BigInteger, ForeignKey('empresas.id'), nullable=False)
    tipo_domicilio_id = Column(BigInteger, ForeignKey('public.tipos_domicilio.id'), nullable=False)
    departamento_id = Column(BigInteger, ForeignKey('public.departamentos.id'), nullable=False)
    municipio_id = Column(BigInteger, ForeignKey('public.municipios.id'), nullable=False)
    direccion_exacta = Column(String(255), nullable=False)
    zona = Column(String(10))
    codigo_postal = Column(String(10))

    tipo_domicilio = relationship("TipoDomicilio")
    departamento = relationship("Departamento")
    municipio = relationship("Municipio")
    empresa = relationship("Empresa", back_populates="domicilios")


class RepresentanteLegal(BigIntPKMixin, SoftDelete, AuditableFull, Base):
    __tablename__ = 'representantes_legales'
    empresa_id = Column(BigInteger, ForeignKey('empresas.id'), nullable=False)
    nombre = Column(String(255), nullable=False)
    dpi = Column(String(20), nullable=False)
    fecha_nombramiento = Column(Date, nullable=False)
    email = Column(String(255))

    empresa = relationship("Empresa", back_populates="representantes")



# ============================================================
# CONTABILIDAD - CuentaContable CON SoftDelete
# ============================================================
class CuentaContable(AuditableFull, BigIntPKMixin, SoftDelete, Base):
    __tablename__ = "plan_cuentas"
    __table_args__ = (
        UniqueConstraint('codigo', 'empresa_id', name='plan_cuentas_codigo_empresa_unique'),
    )
    codigo = Column(String(20), nullable=False, index=True)
    nombre = Column(String(255), nullable=False)
    tipo = Column(String(20), nullable=False)
    naturaleza = Column(String(10), nullable=False)
    acepta_tercero = Column(Boolean, default=False)
    nivel = Column(Integer, default=1)
    cuenta_padre_id = Column(BigInteger, ForeignKey("plan_cuentas.id"), nullable=True)
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=False)
    
    empresa = relationship("Empresa", foreign_keys=[empresa_id])
    # ✅ CORREGIDO: Usar string en lugar de referencia directa
    cuenta_padre = relationship(
        "CuentaContable",
        remote_side="CuentaContable.id",  # ✅ String en lugar de [id]
        foreign_keys=[cuenta_padre_id],
        backref="cuentas_hijas"
    )

# ============================================================
# PARTIDAS - SIN SoftDelete (requisitos legales contables)
# ============================================================
class Partida(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "partidas"
    
    numero_poliza = Column(String(50), nullable=True)
    fecha = Column(Date, nullable=False, index=True)
    descripcion = Column(Text, nullable=False)
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=False, index=True)
    fue_revertida = Column(Boolean, default=False)
    partida_reversion_id = Column(BigInteger, ForeignKey("partidas.id"), nullable=True)
    tipo_origen = Column(String(50), default='manual', nullable=False)

    empresa = relationship("Empresa")
    detalles = relationship("DetallePartida", back_populates="partida", cascade="all, delete-orphan")


class DetallePartida(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "detalle_partidas"
    
    partida_id = Column(BigInteger, ForeignKey("partidas.id", ondelete="CASCADE"), nullable=False, index=True)
    cuenta_id = Column(BigInteger, ForeignKey("plan_cuentas.id"), nullable=False, index=True)
    tipo_movimiento = Column(String(10), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)

    partida = relationship("Partida", back_populates="detalles")
    cuenta = relationship("CuentaContable")


class Secuencia(BigIntPKMixin,  Base):
    __tablename__ = "secuencias"
    __table_args__ = (
        UniqueConstraint('entidad', 'empresa_id', name='uq_secuencias_entidad_empresa'),
    )
    entidad = Column(String(50), nullable=False)
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=False)
    contador = Column(Integer, default=1)

class PeriodoFiscal(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "periodos_fiscales"
    nombre = Column(String(50), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    cerrado = Column(Boolean, default=False, nullable=False)
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=False)
    empresa = relationship("Empresa")

# ============================================================
# FACTURAS - SIN SoftDelete (requisitos legales SAT)
# ============================================================
class FacturaElectronica(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "facturas_electronicas"
    
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=False, index=True)
    xml_original = Column(Text, nullable=False)
    xml_filename = Column(String(255), nullable=True)
    numero_autorizacion = Column(String(50), nullable=False)
    autorizacion_uuid = Column(String(50), nullable=True)
    serie = Column(String(20), nullable=True)
    numero = Column(String(20), nullable=False)
    tipo_documento = Column(String(10), nullable=True)
    moneda = Column(String(5), nullable=True)
    retencion_iva = Column(Numeric(12, 2), default=0, server_default="0")
    retencion_isr = Column(Numeric(12, 2), default=0, server_default="0")
    clasificacion_gasto_sat = Column(String(50), default='NORMAL', server_default="'NORMAL'")
    es_importacion = Column(Boolean, default=False, server_default="false")
    requiere_revision_manual = Column(Boolean, default=False, server_default="false", nullable=False)
    
    tipo_documento_id = Column(BigInteger, ForeignKey(TipoDTE.id), nullable=True, index=True)
    moneda_id = Column(BigInteger, ForeignKey(CatalogoMoneda.id), nullable=True, index=True)
    
    fecha_emision = Column(DateTime(timezone=True), nullable=False, index=True)
    emisor_nit = Column(String(15), nullable=False)
    emisor_nombre = Column(String(255), nullable=False)
    receptor_nit = Column(String(15), nullable=False)
    receptor_nombre = Column(String(255), nullable=False)
    
    total_exento = Column(Numeric(12, 2), default=0)
    total_gravado = Column(Numeric(12, 2), default=0)
    total_iva = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), nullable=False)
    tipo_cambio = Column(Numeric(10, 5), nullable=True)
    
    total_gravado_gtq = Column(Numeric(15, 2), nullable=False)
    total_iva_gtq = Column(Numeric(15, 2), nullable=False)
    total_exento_gtq = Column(Numeric(15, 2), default=0)
    total_gtq = Column(Numeric(15, 2), nullable=False)
    
    total_gravado_bienes = Column(Numeric(12, 2), default=0)
    total_iva_bienes = Column(Numeric(12, 2), default=0)
    total_gravado_servicios = Column(Numeric(12, 2), default=0)
    total_iva_servicios = Column(Numeric(12, 2), default=0)
    total_gravado_bienes_gtq = Column(Numeric(15, 2), default=0)
    total_iva_bienes_gtq = Column(Numeric(15, 2), default=0)
    total_gravado_servicios_gtq = Column(Numeric(15, 2), default=0)
    total_iva_servicios_gtq = Column(Numeric(15, 2), default=0)
    
    es_exportacion = Column(Boolean, default=False)
    pais_destino_exportacion = Column(String(100), nullable=True)
    nombre_comercial = Column(String(255), nullable=True)
    tipo_operacion = Column(String(10), nullable=False, default='Compra')
    estado = Column(String(20), nullable=False, default='Activa')
    fecha_anulacion = Column(DateTime(timezone=True), nullable=True)
    validado = Column(Boolean, server_default="false", default=False)
    fecha_validacion = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    empresa = relationship("Empresa")
    detalles = relationship("FacturaDetalle", back_populates="factura", cascade="all, delete-orphan")
    tipo_documento_rel = relationship(TipoDTE, lazy="select")
    moneda_rel = relationship(CatalogoMoneda, lazy="select")
    impuestos_especiales = relationship(
        "FacturaImpuestoEspecial",
        back_populates="factura",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class FacturaImpuestoEspecial(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "facturas_impuestos_especiales"
    factura_id = Column(BigInteger, ForeignKey("facturas_electronicas.id"), nullable=False, index=True)
    catalogo_id = Column(
        BigInteger,
        ForeignKey("public.catalogo_impuestos_especiales.id"),
        nullable=False,
        index=True
    )
    monto = Column(Numeric(12, 2), nullable=False, server_default="0")

    factura = relationship("FacturaElectronica", back_populates="impuestos_especiales")
    catalogo = relationship("CatalogoImpuestoEspecial", lazy="select")


class FacturaDetalle(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "factura_detalles"
    factura_id = Column(BigInteger, ForeignKey("facturas_electronicas.id", ondelete="CASCADE"), nullable=False, index=True)
    cantidad = Column(Numeric(12, 4), nullable=False)
    descripcion = Column(String(500), nullable=False)
    precio_unitario = Column(Numeric(12, 2), nullable=False)
    total_linea = Column(Numeric(12, 2), nullable=False)
    iva_linea = Column(Numeric(12, 2), default=0)
    precio_unitario_gtq = Column(Numeric(12, 2), nullable=False)
    total_linea_gtq = Column(Numeric(12, 2), nullable=False)
    iva_linea_gtq = Column(Numeric(12, 2), default=0)
    bien_o_servicio = Column(String(1), default='B', server_default='B')

    factura = relationship("FacturaElectronica", back_populates="detalles")


# ============================================================
# LIBROS SAT - SIN SoftDelete (libros oficiales SAT)
# ============================================================
class SatLibro(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "sat_libros"
    empresa_id = Column(BigInteger, ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    tipo_libro_id = Column(BigInteger, ForeignKey("public.tipos_libro.id"), nullable=False)
    regimen_fiscal_id = Column(BigInteger, ForeignKey("public.regimenes_fiscales.id"), nullable=False)
    estado_id = Column(BigInteger, ForeignKey("public.estados_libro.id"), nullable=False)
    anio_periodo = Column(SmallInteger, nullable=False)
    mes_periodo = Column(SmallInteger, nullable=False)
    total_lineas = Column(Integer, default=0, server_default="0")
    total_exento = Column(Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    total_base_imponible = Column(Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    total_iva = Column(Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    total_monto = Column(Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    finalizado_por = Column(BigInteger, nullable=True)
    finalizado_el = Column(DateTime(timezone=True), nullable=True)

    tipo_libro = relationship("TipoLibro", foreign_keys=[tipo_libro_id])
    regimen = relationship("RegimenFiscal", foreign_keys=[regimen_fiscal_id])
    estado = relationship(EstadoLibro, foreign_keys=[estado_id])
    lineas = relationship("SatLibroLinea", back_populates="libro", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("mes_periodo BETWEEN 1 AND 12", name="chk_sat_libros_mes_periodo"),
        UniqueConstraint("empresa_id", "tipo_libro_id", "regimen_fiscal_id", "anio_periodo", "mes_periodo", name="uq_sat_libros_periodo"),
        Index("idx_sat_libros_empresa_periodo", "empresa_id", "anio_periodo", "mes_periodo"),
    )


class SatLibroLinea(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "sat_libros_lineas"
    libro_id = Column(BigInteger, ForeignKey("sat_libros.id", ondelete="CASCADE"), nullable=False, index=True)
    factura_id = Column(BigInteger, nullable=False)
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
    credito_fiscal = Column(Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    debito_fiscal = Column(Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")

    libro = relationship("SatLibro", back_populates="lineas")

    __table_args__ = (
        UniqueConstraint("libro_id", "numero_secuencia", name="uq_sat_libros_lineas_secuencia"),
        Index("idx_sat_libros_lineas_libro", "libro_id"),
    )

# ============================================================
# ACTIVOS FIJOS - ActivoFijo CON SoftDelete
# ============================================================
class ActivoFijo(BigIntPKMixin, AuditableFull, SoftDelete, Base):
    __tablename__ = "activos_fijos"
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=False, index=True)
    categoria_id = Column(BigInteger, ForeignKey("public.categorias_activos_fijos.id"), nullable=False)
    codigo_interno = Column(String(50), nullable=False)
    descripcion = Column(String(255), nullable=False)
    fecha_adquisicion = Column(Date, nullable=False)
    valor_costo = Column(Numeric(15, 2), nullable=False)
    valor_residual = Column(Numeric(15, 2), nullable=False, server_default="0.00")
    tasa_depreciacion_anual_aplicada = Column(Numeric(5, 2), nullable=False)
    vida_util_meses_aplicada = Column(Integer, nullable=False)
    cuenta_gasto_id = Column(BigInteger, ForeignKey("plan_cuentas.id"), nullable=True)
    cuenta_depreciacion_acumulada_id = Column(BigInteger, ForeignKey("plan_cuentas.id"), nullable=True)
    estado = Column(String(30), nullable=False, default=EstadoActivoFijoEnum.activo.value)

    empresa = relationship("Empresa")
    categoria = relationship("CategoriaActivoFijo", foreign_keys=[categoria_id], lazy="select")
    cuenta_gasto = relationship("CuentaContable", foreign_keys=[cuenta_gasto_id])
    cuenta_depreciacion_acumulada = relationship("CuentaContable", foreign_keys=[cuenta_depreciacion_acumulada_id])
    historial_depreciacion = relationship("DepreciacionActivo", back_populates="activo", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "tasa_depreciacion_anual_aplicada >= 0 AND tasa_depreciacion_anual_aplicada <= 100",
            name="chk_activos_fijos_tasa_valida"
        ),
    )


class DepreciacionActivo(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "depreciacion_activos"
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=False, index=True)
    activo_id = Column(BigInteger, ForeignKey("activos_fijos.id"), nullable=False)
    anio_periodo = Column(SmallInteger, nullable=False)
    mes_periodo = Column(SmallInteger, nullable=False)
    monto_depreciacion_mes = Column(Numeric(15, 2), nullable=False)
    depreciacion_acumulada_hasta_fecha = Column(Numeric(15, 2), nullable=False)
    valor_en_libros = Column(Numeric(15, 2), nullable=False)
    partida_id = Column(BigInteger, ForeignKey("partidas.id"), nullable=True)

    empresa = relationship("Empresa")
    activo = relationship("ActivoFijo", back_populates="historial_depreciacion")
    partida = relationship("Partida")

    __table_args__ = (
        UniqueConstraint("activo_id", "anio_periodo", "mes_periodo", name="uq_depreciacion_activo_periodo"),
        CheckConstraint("mes_periodo BETWEEN 1 AND 12", name="chk_depreciacion_mes_valido"),
        Index("idx_depreciacion_activos_empresa_periodo", "empresa_id", "anio_periodo", "mes_periodo"),
    )

# ============================================================
# DECLARACIONES - SIN SoftDelete (declaraciones oficiales SAT)
# ============================================================
class DeclaracionImpuesto(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "declaraciones_impuesto"
    
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=False, index=True)
    formulario_sat_id = Column(BigInteger, ForeignKey("public.formularios_sat.id"), nullable=False)
    anio = Column(SmallInteger, nullable=False, index=True)
    mes = Column(SmallInteger, nullable=False, index=True)
    estado = Column(String(20), default='BORRADOR', nullable=False)
    total_debito_fiscal = Column(Numeric(15, 2), default=0, server_default="0")
    total_credito_fiscal = Column(Numeric(15, 2), default=0, server_default="0")
    impuesto_determinado = Column(Numeric(15, 2), default=0, server_default="0")
    remanente_periodo_anterior = Column(Numeric(15, 2), default=0, server_default="0")
    remanente_siguiente_periodo = Column(Numeric(15, 2), default=0, server_default="0")
    impuesto_a_pagar = Column(Numeric(15, 2), default=0, server_default="0")
    finalizado_por = Column(BigInteger, nullable=True)
    fecha_cierre = Column(DateTime(timezone=True), nullable=True)

    empresa = relationship("Empresa")
    detalles = relationship("DetalleDeclaracionImpuesto", back_populates="declaracion", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("empresa_id", "formulario_sat_id", "anio", "mes", name="uq_declaracion_periodo"),
    )


class DetalleDeclaracionImpuesto(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "detalles_declaracion_impuesto"
    
    declaracion_id = Column(BigInteger, ForeignKey("declaraciones_impuesto.id", ondelete="CASCADE"), nullable=False)
    casilla_sat_id = Column(BigInteger, ForeignKey("public.casillas_sat.id"), nullable=False)
    base_imponible = Column(Numeric(15, 2), default=0, server_default="0")
    monto_impuesto = Column(Numeric(15, 2), default=0, server_default="0")
    es_ajuste_manual = Column(Boolean, default=False, server_default="false")
    motivo_ajuste = Column(Text, nullable=True)
    ajustado_por = Column(BigInteger, nullable=True)

    declaracion = relationship("DeclaracionImpuesto", back_populates="detalles")
    facturas_asociadas = relationship("DeclaracionImpuestoFactura", back_populates="detalle", cascade="all, delete-orphan")
    casilla = relationship(
        "CasillaSat",
        primaryjoin="DetalleDeclaracionImpuesto.casilla_sat_id == foreign(CasillaSat.id)",
        uselist=False,
        viewonly=True
    )


class DeclaracionImpuestoFactura(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "declaraciones_impuesto_facturas"
    
    detalle_declaracion_id = Column(BigInteger, ForeignKey("detalles_declaracion_impuesto.id", ondelete="CASCADE"), nullable=False)
    factura_id = Column(BigInteger, ForeignKey("facturas_electronicas.id"), nullable=False)
    base_asignada = Column(Numeric(15, 2), default=0, server_default="0")
    impuesto_asignado = Column(Numeric(15, 2), default=0, server_default="0")

    detalle = relationship("DetalleDeclaracionImpuesto", back_populates="facturas_asociadas")
    factura = relationship("FacturaElectronica")

    __table_args__ = (
        UniqueConstraint("detalle_declaracion_id", "factura_id", name="uq_detalle_factura"),
    )

# ============================================================
# INVENTARIOS - Bodegas y Productos CON SoftDelete
# Tomas, Items e Importaciones SIN SoftDelete (valor legal SAT)
# ============================================================

class InventarioBodega(BigIntPKMixin, AuditableFull, SoftDelete, Base):
    __tablename__ = "inventarios_bodegas"
    __table_args__ = (
        UniqueConstraint("tenant_id", "empresa_id", "codigo", name="uq_inventarios_bodegas_codigo"),
        Index("idx_inventarios_bodegas_empresa", "tenant_id", "empresa_id"),
    )
    tenant_id = Column(BigInteger, ForeignKey("public.tenants.id"), nullable=False, index=True)
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=False, index=True)
    codigo = Column(String(20), nullable=False)
    nombre = Column(String(100), nullable=False)
    ubicacion = Column(String(200))
    empresa = relationship("Empresa")
    items = relationship("InventarioItem", back_populates="bodega")


class InventarioProducto(BigIntPKMixin, AuditableFull, SoftDelete, Base):
    __tablename__ = "inventarios_productos"
    __table_args__ = (
        UniqueConstraint("tenant_id", "empresa_id", "codigo", name="uq_inventarios_productos_codigo"),
        Index("idx_inventarios_productos_empresa", "tenant_id", "empresa_id"),
    )
    tenant_id = Column(BigInteger, ForeignKey("public.tenants.id"), nullable=False, index=True)
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=False, index=True)
    codigo = Column(String(50))
    descripcion = Column(String(255), nullable=False)
    unidad_medida = Column(String(20), default="UND", nullable=False, server_default="'UND'")
    cuenta_inventario_id = Column(BigInteger, ForeignKey("plan_cuentas.id"), nullable=True)
    empresa = relationship("Empresa")
    cuenta_inventario = relationship("CuentaContable", foreign_keys=[cuenta_inventario_id])
    items = relationship("InventarioItem", back_populates="producto")


class InventarioToma(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "inventarios_tomas"
    __table_args__ = (
        UniqueConstraint("tenant_id", "empresa_id", "anio_periodo", "mes_periodo", name="uq_inventarios_tomas_periodo"),
        CheckConstraint("estado IN ('BORRADOR', 'CONFIRMADO', 'CONTABILIZADO')", name="chk_inventarios_tomas_estado"),
        CheckConstraint("tipo IN ('FISCAL', 'INTERNO', 'AJUSTE')", name="chk_inventarios_tomas_tipo"),
        CheckConstraint("metodo_valuacion IN ('COSTO_PROMEDIO', 'PEPS', 'IDENTIFICACION_ESPECIFICA')", name="chk_inventarios_tomas_metodo"),
        CheckConstraint("mes_periodo BETWEEN 1 AND 12", name="chk_inventarios_tomas_mes_valido"),
        Index("idx_inventarios_tomas_empresa_periodo", "tenant_id", "empresa_id", "anio_periodo", "mes_periodo"),
    )
    tenant_id = Column(BigInteger, ForeignKey("public.tenants.id"), nullable=False, index=True)
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=False, index=True)
    anio_periodo = Column(SmallInteger, nullable=False, index=True)
    mes_periodo = Column(SmallInteger, nullable=False, index=True)
    fecha_corte = Column(Date, nullable=False)
    tipo = Column(String(20), nullable=False, default="FISCAL", server_default="'FISCAL'")
    metodo_valuacion = Column(String(30), nullable=False, default="COSTO_PROMEDIO", server_default="'COSTO_PROMEDIO'")
    estado = Column(String(20), nullable=False, default="BORRADOR", server_default="'BORRADOR'")
    observaciones = Column(Text)
    partida_ajuste_id = Column(BigInteger, ForeignKey("partidas.id", ondelete="SET NULL"), nullable=True)
    total_items = Column(Integer, default=0, server_default="0")
    valor_total = Column(Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    empresa = relationship("Empresa")
    partida_ajuste = relationship("Partida")
    items = relationship("InventarioItem", back_populates="toma", cascade="all, delete-orphan")
    importaciones = relationship("InventarioImportacion", back_populates="toma", cascade="all, delete-orphan")


class InventarioItem(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "inventarios_items"
    __table_args__ = (Index("idx_inventarios_items_toma", "toma_id"), Index("idx_inventarios_items_codigo", "codigo"))
    toma_id = Column(BigInteger, ForeignKey("inventarios_tomas.id", ondelete="CASCADE"), nullable=False, index=True)
    producto_id = Column(BigInteger, ForeignKey("inventarios_productos.id", ondelete="SET NULL"), nullable=True)
    bodega_id = Column(BigInteger, ForeignKey("inventarios_bodegas.id", ondelete="SET NULL"), nullable=True)
    codigo = Column(String(50), index=True)
    descripcion = Column(String(255), nullable=False)
    unidad_medida = Column(String(20), default="UND", server_default="'UND'")
    cantidad = Column(Numeric(15, 4), nullable=False)
    costo_unitario = Column(Numeric(15, 4), nullable=False)
    costo_total = Column(Numeric(15, 2), nullable=False)
    bodega_codigo = Column(String(20))
    toma = relationship("InventarioToma", back_populates="items")
    producto = relationship("InventarioProducto", back_populates="items")
    bodega = relationship("InventarioBodega", back_populates="items")


class InventarioImportacion(BigIntPKMixin, AuditableFull, Base):
    __tablename__ = "inventarios_importaciones"
    __table_args__ = (Index("idx_inventarios_importaciones_toma", "toma_id"),)
    toma_id = Column(BigInteger, ForeignKey("inventarios_tomas.id", ondelete="CASCADE"), nullable=False, index=True)
    archivo_original = Column(String(255), nullable=False)
    formato = Column(String(10), nullable=False)
    modo = Column(String(20), nullable=False, default="REEMPLAZAR")
    filas_procesadas = Column(Integer, nullable=False, server_default="0")
    filas_validas = Column(Integer, nullable=False, server_default="0")
    filas_con_error = Column(Integer, nullable=False, server_default="0")
    errores = Column(JSONB)
    toma = relationship("InventarioToma", back_populates="importaciones")