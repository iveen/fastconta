"""
Mixins de auditoría reutilizables para todos los modelos.

Uso:
    class MiModelo(AuditableFull, Base):
        __tablename__ = "mi_tabla"
        # ... tus campos ...

Tipos disponibles:
    - AuditableFull: created_at, created_by, updated_at, updated_by
    - AuditableCreate: Solo created_at, created_by (para catálogos inmutables)
"""

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class AuditableCreate:
    """
    Mixin para modelos que solo necesitan auditoría de creación.
    Ideal para catálogos que rara vez se modifican (ej: Secciones SAT, Reglas).
    """
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("public.users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Usuario que creó el registro"
    )


class AuditableFull(AuditableCreate):
    """
    Mixin completo de auditoría: creación + modificación.
    Ideal para modelos transaccionales (declaraciones, facturas, partidas).
    """
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
        onupdate=func.now(),
        index=True
    )
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("public.users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Usuario que modificó el registro por última vez"
    )