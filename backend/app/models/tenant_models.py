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
from app.models.global_models import (
    TipoDTE, CatalogoMoneda, 
    TipoLibro, RegimenFiscal, EstadoLibro, TipoDomicilio, TipoPersona, Departamento, Municipio,
    ActividadEconomicaSAT
)
from datetime import date, datetime



class Empresa(Base):
    __tablename__ = "empresas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

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

    # Gestión de Fechas y Estado
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relaciones (Estructura de Normalización)
    regimen_fiscal = relationship("RegimenFiscal", foreign_keys=[regimen_fiscal_id])
    tipo_persona = relationship("TipoPersona", foreign_keys=[tipo_persona_id])
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
    
    # Relaciones
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
    
    tipo_libro_id = Column(UUID(as_uuid=True), ForeignKey("public.tipos_libro.id"), nullable=False)
    regimen_fiscal_id = Column(UUID(as_uuid=True), ForeignKey("public.regimenes_fiscales.id"), nullable=False)
    estado_id = Column(UUID(as_uuid=True), ForeignKey("public.estados_libro.id"), nullable=False)
    
    anio_periodo: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False)
    mes_periodo: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False)
    
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

    tipo_libro = relationship("TipoLibro", foreign_keys=[tipo_libro_id])
    regimen = relationship("RegimenFiscal", foreign_keys=[regimen_fiscal_id])
    estado = relationship("EstadoLibro", foreign_keys=[estado_id])

    # Restricciones de tabla e Índices en español
    __table_args__ = (
        sa.CheckConstraint("mes_periodo BETWEEN 1 AND 12", name="chk_sat_libros_mes_periodo"),
        
        sa.UniqueConstraint(
            "empresa_id", 
            "tipo_libro_id", 
            "regimen_fiscal_id",  
            "anio_periodo", 
            "mes_periodo", 
            name="uq_sat_libros_periodo"
        ),
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