import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    schema_name = Column(String(63), unique=True, nullable=False)
    nit = Column(String(15), unique=True, nullable=False)       # <-- añadir
    plan = Column(String(20), default="freemium", nullable=False)  # <-- añadir
    max_empresas = Column(Integer, default=5, nullable=False)     # <-- añadir
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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
    