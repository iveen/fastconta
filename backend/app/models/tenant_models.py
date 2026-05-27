# app/models/tenant_models.py
import uuid
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Numeric, Enum as SAEnum, \
    Date, ForeignKey, UniqueConstraint, Sequence
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base
import sqlalchemy as sa
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from app.models.global_models import TipoDTE, CatalogoMoneda
from datetime import date, datetime

class Empresa(Base):
    __tablename__ = "empresas"
    # Nota: no especificamos schema aquí, será asignado dinámicamente por search_path
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(255), nullable=False)
    nit = Column(String(20), unique=True, nullable=False)
    direccion = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


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
class TipoLibro(str, Enum):
    COMPRAS = "compras"
    VENTAS = "ventas"


class RegimenFiscal(str, Enum):
    GENERAL = "general"
    PEQUENO_CONTRIBUYENTE = "pequeno_contribuyente"


class EstadoLibro(str, Enum):
    BORRADOR = "borrador"
    FINALIZADO = "finalizado"
    PRESENTADO = "presentado"


class SatLibro(Base):
    __tablename__ = "sat_libros"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
    )
    
    empresa_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("empresas.id", ondelete="RESTRICT"), 
        nullable=False
    )
    
    tipo_libro: Mapped[TipoLibro] = mapped_column(
        sa.Enum(TipoLibro, native_enum=False), 
        nullable=False
    )
    regimen_fiscal: Mapped[RegimenFiscal] = mapped_column(
        sa.Enum(RegimenFiscal, native_enum=False), 
        nullable=False
    )
    
    anio_periodo: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False)
    mes_periodo: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False)
    
    estado: Mapped[EstadoLibro] = mapped_column(
        sa.Enum(EstadoLibro, native_enum=False),
        default=EstadoLibro.BORRADOR,
        server_default="'borrador'",
    )
    
    total_lineas: Mapped[int] = mapped_column(sa.Integer, default=0, server_default="0")
    total_exento: Mapped[Decimal] = mapped_column(sa.Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    total_base_imponible: Mapped[Decimal] = mapped_column(sa.Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    total_iva: Mapped[Decimal] = mapped_column(sa.Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    total_monto: Mapped[Decimal] = mapped_column(sa.Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    
    finalizado_por: Mapped[Optional[uuid.UUID]] = mapped_column(sa.UUID(as_uuid=True), nullable=True)
    finalizado_el: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    creado_el: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), 
        default=datetime.utcnow, 
        server_default=sa.func.now()
    )

    # Relación uno a muchos con las líneas del libro
    lineas: Mapped[List["SatLibroLinea"]] = relationship(
        back_populates="libro", 
        cascade="all, delete-orphan"
    )

    # Restricciones de tabla e Índices en español
    __table_args__ = (
        sa.CheckConstraint("mes_periodo BETWEEN 1 AND 12", name="chk_sat_libros_mes_periodo"),
        sa.UniqueConstraint("empresa_id", "tipo_libro", "anio_periodo", "mes_periodo", name="uq_sat_libros_periodo"),
        sa.Index("idx_sat_libros_empresa_periodo", "empresa_id", "anio_periodo", "mes_periodo"),
    )


class SatLibroLinea(Base):
    __tablename__ = "sat_libros_lineas"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
    )
    libro_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("sat_libros.id", ondelete="CASCADE"), 
        nullable=False
    )
    factura_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False)
    
    numero_secuencia: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    fecha_documento: Mapped[date] = mapped_column(sa.Date, nullable=False)
    numero_documento: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    nit: Mapped[Optional[str]] = mapped_column(sa.String(20), nullable=True)
    razon_social: Mapped[Optional[str]] = mapped_column(sa.String(255), nullable=True)
    
    es_exento: Mapped[bool] = mapped_column(sa.Boolean, default=False, server_default="false")
    es_exonerado: Mapped[bool] = mapped_column(sa.Boolean, default=False, server_default="false")
    
    base_imponible: Mapped[Decimal] = mapped_column(sa.Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    monto_exento: Mapped[Decimal] = mapped_column(
        sa.Numeric(15, 2), 
        default=Decimal("0.00"), 
        server_default="0.00"
    )
    monto_iva: Mapped[Decimal] = mapped_column(sa.Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    monto_total: Mapped[Decimal] = mapped_column(sa.Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    
    # Columnas específicas del Régimen Normal de la SAT
    credito_fiscal: Mapped[Decimal] = mapped_column(sa.Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")
    debito_fiscal: Mapped[Decimal] = mapped_column(sa.Numeric(15, 2), default=Decimal("0.00"), server_default="0.00")

    # Relación inversa hacia el encabezado del libro
    libro: Mapped["SatLibro"] = relationship(back_populates="lineas")

    # Restricciones de tabla e Índices en español
    __table_args__ = (
        sa.UniqueConstraint("libro_id", "numero_secuencia", name="uq_sat_libros_lineas_secuencia"),
        sa.Index("idx_sat_libros_lineas_libro", "libro_id"),
    )