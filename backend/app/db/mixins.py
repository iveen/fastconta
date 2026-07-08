"""
Mixins de auditoría reutilizables para todos los modelos.
"""
import uuid

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Identity
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class BigIntPKMixin:
    """
    Mixin que agrega:
    - id: BIGINT como PK interna (óptimo para B-Tree y JOINs)
    - public_id: UUID único como PK pública (para la API)
    """
    id = Column(BigInteger, Identity(always=True), primary_key=True)
    public_id = Column(
        UUID(as_uuid=True), 
        default=uuid.uuid4, 
        unique=True, 
        nullable=False, 
        index=True
    )


class SoftDelete:
    """
    Mixin para modelos que necesitan soft delete.
    Reglas de uso en FastConta:
    ✅ USAR EN: Catálogos, configuraciones, usuarios, empresas
    ❌ NO USAR EN: Tablas transaccionales contables (partidas, facturas, declaraciones)
    """
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Indica si el registro está activo (soft delete)"
    )
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Fecha y hora en que el registro fue eliminado (soft delete)"
    )


class AuditableCreate:
    """
    Mixin para modelos que solo necesitan auditoría de creación.
    """
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )
    # ✅ CORREGIDO: Ahora es BigInteger (apunta a users.id)
    created_by = Column(
        BigInteger,
        ForeignKey("public.users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Usuario que creó el registro"
    )


class AuditableFull(AuditableCreate):
    """
    Mixin completo de auditoría: creación + modificación.
    """
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
        onupdate=func.now(),
        index=True
    )
    # ✅ CORREGIDO: Ahora es BigInteger (apunta a users.id)
    updated_by = Column(
        BigInteger,
        ForeignKey("public.users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Usuario que modificó el registro por última vez"
    )