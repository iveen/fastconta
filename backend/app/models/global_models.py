import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text
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
    
    # 2. Contacto del Responsable (Crucial para notificaciones y soporte)
    admin_email = Column(String(255), nullable=False) 
    
    # 3. Configuración Comercial (Planes y Límites)
    plan = Column(String(20), default="freemium", nullable=False)
    max_empresas = Column(Integer, default=5, nullable=False)     # Límite de empresas clientes
    max_usuarios = Column(Integer, default=3, nullable=False)     # Límite de contadores en la firma
    
    # 4. Estado
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    users = relationship("User", back_populates="tenant")

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("public.tenants.id"), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # admin, contador, auxiliar
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="users")

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
    nombre = Column(String(50), nullable=False)

class RegimenFiscal(Base):
    __tablename__ = "regimenes_fiscales"
    __table_args__ = {"schema": "public"}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False)

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
