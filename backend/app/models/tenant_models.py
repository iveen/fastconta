# app/models/tenant_models.py
import uuid
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Numeric, Enum as SAEnum, \
    Date, ForeignKey, UniqueConstraint, Sequence
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.global_models import TipoDTE, CatalogoMoneda

class Empresa(Base):
    __tablename__ = "empresas"
    # Nota: no especificamos schema aquí, será asignado dinámicamente por search_path
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(255), nullable=False)
    nit = Column(String(20), unique=True, nullable=False)
    direccion = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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
    cuenta_padre_id = Column(UUID(as_uuid=True), nullable=True)
    activa = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    empresa = relationship("Empresa")

class Partida(Base):
    __tablename__ = "partidas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero = Column(Integer, Sequence('partidas_numero_seq'), unique=True, nullable=False)
    numero_poliza = Column(String(50), nullable=True)
    fecha = Column(Date, nullable=False)
    descripcion = Column(Text, nullable=False)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    empresa = relationship("Empresa")
    detalles = relationship("DetallePartida", back_populates="partida", cascade="all, delete-orphan")

class DetallePartida(Base):
    __tablename__ = "detalle_partidas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partida_id = Column(UUID(as_uuid=True), ForeignKey("partidas.id", ondelete="CASCADE"), nullable=False)
    cuenta_id = Column(UUID(as_uuid=True), ForeignKey("plan_cuentas.id"), nullable=False)
    tipo_movimiento = Column(String(10), nullable=False)  # "debe" o "haber"
    monto = Column(Numeric(12, 2), nullable=False)

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

    total_gravado = Column(Numeric(12,2), default=0)
    total_iva = Column(Numeric(12,2), default=0)
    total_exento = Column(Numeric(12,2), default=0)
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