# app/models/tenant_models.py
import uuid
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Numeric, Enum as SAEnum, \
    Date, ForeignKey, UniqueConstraint, Sequence
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    nombre = Column(String(255), nullable=False)
    tipo = Column(String(20), nullable=False)          # <-- String en lugar de Enum
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
    numero_poliza = Column(String(50), unique=True, nullable=True)
    fecha = Column(Date, nullable=False)
    descripcion = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
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