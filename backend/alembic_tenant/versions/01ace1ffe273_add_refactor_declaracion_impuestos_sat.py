"""add_refactor_declaracion_impuestos_sat

Revision ID: 01ace1ffe273
Revises: 0df0318bd6da
Create Date: 2026-06-18 08:50:41.765956

"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '01ace1ffe273'
down_revision: Union[str, None] = '0df0318bd6da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return   
    # =========================================================================
    # NOTA IMPORTANTE: Las tablas de declaraciones están en schemas dinámicos
    # de cada tenant. Esta migración NO especifica schema, por lo que usa el
    # search_path de la conexión.
    #
    # Para aplicar a TODOS los tenants, ejecutar esta migración cambiando el
    # search_path antes de cada ejecución:
    #
    #   SET search_path TO tenant_abc, public;
    #   -- luego ejecutar la migración
    #
    # O usar un script que itere sobre todos los schemas de tenant.
    # =========================================================================

    # -------------------------------------------------------------------------
    # 1. DeclaracionesImpuesto: Ya tiene created_at y updated_at
    #    Solo necesita created_by y updated_by
    # -------------------------------------------------------------------------
    op.add_column(
        'declaraciones_impuesto',
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        'declaraciones_impuesto',
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_declaraciones_impuesto_created_by',
        'declaraciones_impuesto', 'users',
        ['created_by'], ['id'],
        referent_schema='public',
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_declaraciones_impuesto_updated_by',
        'declaraciones_impuesto', 'users',
        ['updated_by'], ['id'],
        referent_schema='public',
        ondelete='SET NULL'
    )
    op.create_index(
        'idx_declaraciones_impuesto_created_by',
        'declaraciones_impuesto',
        ['created_by'],
        unique=False
    )
    op.create_index(
        'idx_declaraciones_impuesto_updated_by',
        'declaraciones_impuesto',
        ['updated_by'],
        unique=False
    )

    # -------------------------------------------------------------------------
    # 2. DetallesDeclaracionImpuesto: Necesita los 4 campos del mixin
    # -------------------------------------------------------------------------
    op.add_column(
        'detalles_declaracion_impuesto',
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False)
    )
    op.add_column(
        'detalles_declaracion_impuesto',
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        'detalles_declaracion_impuesto',
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=True)
    )
    op.add_column(
        'detalles_declaracion_impuesto',
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_detalles_declaracion_created_by',
        'detalles_declaracion_impuesto', 'users',
        ['created_by'], ['id'],
        referent_schema='public',
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_detalles_declaracion_updated_by',
        'detalles_declaracion_impuesto', 'users',
        ['updated_by'], ['id'],
        referent_schema='public',
        ondelete='SET NULL'
    )
    op.create_index(
        'idx_detalles_declaracion_created_by',
        'detalles_declaracion_impuesto',
        ['created_by'],
        unique=False
    )
    op.create_index(
        'idx_detalles_declaracion_updated_by',
        'detalles_declaracion_impuesto',
        ['updated_by'],
        unique=False
    )

    # -------------------------------------------------------------------------
    # 3. DeclaracionesImpuestoFactura: Necesita los 4 campos del mixin
    # -------------------------------------------------------------------------
    op.add_column(
        'declaraciones_impuesto_facturas',
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False)
    )
    op.add_column(
        'declaraciones_impuesto_facturas',
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        'declaraciones_impuesto_facturas',
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=True)
    )
    op.add_column(
        'declaraciones_impuesto_facturas',
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_declaraciones_facturas_created_by',
        'declaraciones_impuesto_facturas', 'users',
        ['created_by'], ['id'],
        referent_schema='public',
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_declaraciones_facturas_updated_by',
        'declaraciones_impuesto_facturas', 'users',
        ['updated_by'], ['id'],
        referent_schema='public',
        ondelete='SET NULL'
    )
    op.create_index(
        'idx_declaraciones_facturas_created_by',
        'declaraciones_impuesto_facturas',
        ['created_by'],
        unique=False
    )
    op.create_index(
        'idx_declaraciones_facturas_updated_by',
        'declaraciones_impuesto_facturas',
        ['updated_by'],
        unique=False
    )


def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return   
    # -------------------------------------------------------------------------
    # 3. Revertir DeclaracionesImpuestoFactura
    # -------------------------------------------------------------------------
    op.drop_index('idx_declaraciones_facturas_updated_by', table_name='declaraciones_impuesto_facturas')
    op.drop_index('idx_declaraciones_facturas_created_by', table_name='declaraciones_impuesto_facturas')
    op.drop_constraint('fk_declaraciones_facturas_updated_by', 'declaraciones_impuesto_facturas', type_='foreignkey')
    op.drop_constraint('fk_declaraciones_facturas_created_by', 'declaraciones_impuesto_facturas', type_='foreignkey')
    op.drop_column('declaraciones_impuesto_facturas', 'updated_by')
    op.drop_column('declaraciones_impuesto_facturas', 'updated_at')
    op.drop_column('declaraciones_impuesto_facturas', 'created_by')
    op.drop_column('declaraciones_impuesto_facturas', 'created_at')

    # -------------------------------------------------------------------------
    # 2. Revertir DetallesDeclaracionImpuesto
    # -------------------------------------------------------------------------
    op.drop_index('idx_detalles_declaracion_updated_by', table_name='detalles_declaracion_impuesto')
    op.drop_index('idx_detalles_declaracion_created_by', table_name='detalles_declaracion_impuesto')
    op.drop_constraint('fk_detalles_declaracion_updated_by', 'detalles_declaracion_impuesto', type_='foreignkey')
    op.drop_constraint('fk_detalles_declaracion_created_by', 'detalles_declaracion_impuesto', type_='foreignkey')
    op.drop_column('detalles_declaracion_impuesto', 'updated_by')
    op.drop_column('detalles_declaracion_impuesto', 'updated_at')
    op.drop_column('detalles_declaracion_impuesto', 'created_by')
    op.drop_column('detalles_declaracion_impuesto', 'created_at')

    # -------------------------------------------------------------------------
    # 1. Revertir DeclaracionesImpuesto
    # -------------------------------------------------------------------------
    op.drop_index('idx_declaraciones_impuesto_updated_by', table_name='declaraciones_impuesto')
    op.drop_index('idx_declaraciones_impuesto_created_by', table_name='declaraciones_impuesto')
    op.drop_constraint('fk_declaraciones_impuesto_updated_by', 'declaraciones_impuesto', type_='foreignkey')
    op.drop_constraint('fk_declaraciones_impuesto_created_by', 'declaraciones_impuesto', type_='foreignkey')
    op.drop_column('declaraciones_impuesto', 'updated_by')
    op.drop_column('declaraciones_impuesto', 'created_by')
