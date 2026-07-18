"""add_inventory_tables

Revision ID: aa88ec971526
Revises: 4360f9683f8b
Create Date: 2026-07-18 16:22:17.391892

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'aa88ec971526'
down_revision: Union[str, None] = '4360f9683f8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================
    # 1. INVENTARIOS_BODEGAS (Catálogo con SoftDelete)
    # ============================================================
    op.create_table(
        'inventarios_bodegas',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column('tenant_id', sa.BigInteger(), sa.ForeignKey('public.tenants.id'), nullable=False, index=True),
        sa.Column('empresa_id', sa.BigInteger(), sa.ForeignKey('empresas.id'), nullable=False, index=True),
        sa.Column('codigo', sa.String(20), nullable=False),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('ubicacion', sa.String(200), nullable=True),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', index=True,
                  comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, index=True,
                  comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('created_by', sa.BigInteger(), sa.ForeignKey('public.users.id', ondelete='SET NULL'),
                  nullable=True, index=True, comment='Usuario que creó el registro'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now(), index=True),
        sa.Column('updated_by', sa.BigInteger(), sa.ForeignKey('public.users.id', ondelete='SET NULL'),
                  nullable=True, index=True, comment='Usuario que modificó el registro por última vez'),
        # Constraints
        sa.UniqueConstraint('tenant_id', 'empresa_id', 'codigo', name='uq_inventarios_bodegas_codigo'),
    )
    op.create_index('idx_inventarios_bodegas_empresa', 'inventarios_bodegas', ['tenant_id', 'empresa_id'])

    # ============================================================
    # 2. INVENTARIOS_PRODUCTOS (Catálogo con SoftDelete)
    # ============================================================
    op.create_table(
        'inventarios_productos',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column('tenant_id', sa.BigInteger(), sa.ForeignKey('public.tenants.id'), nullable=False, index=True),
        sa.Column('empresa_id', sa.BigInteger(), sa.ForeignKey('empresas.id'), nullable=False, index=True),
        sa.Column('codigo', sa.String(50), nullable=True),
        sa.Column('descripcion', sa.String(255), nullable=False),
        sa.Column('unidad_medida', sa.String(20), nullable=False, server_default='UND'),
        sa.Column('cuenta_inventario_id', sa.BigInteger(), sa.ForeignKey('plan_cuentas.id'), nullable=True),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', index=True,
                  comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, index=True,
                  comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('created_by', sa.BigInteger(), sa.ForeignKey('public.users.id', ondelete='SET NULL'),
                  nullable=True, index=True, comment='Usuario que creó el registro'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now(), index=True),
        sa.Column('updated_by', sa.BigInteger(), sa.ForeignKey('public.users.id', ondelete='SET NULL'),
                  nullable=True, index=True, comment='Usuario que modificó el registro por última vez'),
        # Constraints
        sa.UniqueConstraint('tenant_id', 'empresa_id', 'codigo', name='uq_inventarios_productos_codigo'),
    )
    op.create_index('idx_inventarios_productos_empresa', 'inventarios_productos', ['tenant_id', 'empresa_id'])

    # ============================================================
    # 3. INVENTARIOS_TOMAS (Transaccional SIN SoftDelete)
    # ============================================================
    op.create_table(
        'inventarios_tomas',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column('tenant_id', sa.BigInteger(), sa.ForeignKey('public.tenants.id'), nullable=False, index=True),
        sa.Column('empresa_id', sa.BigInteger(), sa.ForeignKey('empresas.id'), nullable=False, index=True),
        sa.Column('anio_periodo', sa.SmallInteger(), nullable=False, index=True),
        sa.Column('mes_periodo', sa.SmallInteger(), nullable=False, index=True),
        sa.Column('fecha_corte', sa.Date(), nullable=False),
        sa.Column('tipo', sa.String(20), nullable=False, server_default='FISCAL'),
        sa.Column('metodo_valuacion', sa.String(30), nullable=False, server_default='COSTO_PROMEDIO'),
        sa.Column('estado', sa.String(20), nullable=False, server_default='BORRADOR'),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('partida_ajuste_id', sa.BigInteger(), sa.ForeignKey('partidas.id', ondelete='SET NULL'), nullable=True),
        sa.Column('total_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('valor_total', sa.Numeric(15, 2), nullable=False, server_default='0.00'),
        # AuditableFull
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('created_by', sa.BigInteger(), sa.ForeignKey('public.users.id', ondelete='SET NULL'),
                  nullable=True, index=True, comment='Usuario que creó el registro'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now(), index=True),
        sa.Column('updated_by', sa.BigInteger(), sa.ForeignKey('public.users.id', ondelete='SET NULL'),
                  nullable=True, index=True, comment='Usuario que modificó el registro por última vez'),
        # Constraints
        sa.UniqueConstraint('tenant_id', 'empresa_id', 'anio_periodo', 'mes_periodo',
                            name='uq_inventarios_tomas_periodo'),
        sa.CheckConstraint(
            "estado IN ('BORRADOR', 'CONFIRMADO', 'CONTABILIZADO')",
            name='chk_inventarios_tomas_estado'
        ),
        sa.CheckConstraint(
            "tipo IN ('FISCAL', 'INTERNO', 'AJUSTE')",
            name='chk_inventarios_tomas_tipo'
        ),
        sa.CheckConstraint(
            "metodo_valuacion IN ('COSTO_PROMEDIO', 'PEPS', 'IDENTIFICACION_ESPECIFICA')",
            name='chk_inventarios_tomas_metodo'
        ),
        sa.CheckConstraint(
            'mes_periodo BETWEEN 1 AND 12',
            name='chk_inventarios_tomas_mes_valido'
        ),
    )
    op.create_index(
        'idx_inventarios_tomas_empresa_periodo',
        'inventarios_tomas',
        ['tenant_id', 'empresa_id', 'anio_periodo', 'mes_periodo']
    )
    op.create_index('idx_inventarios_tomas_estado', 'inventarios_tomas', ['estado'])

    # ============================================================
    # 4. INVENTARIOS_ITEMS (Transaccional SIN SoftDelete)
    # ============================================================
    op.create_table(
        'inventarios_items',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column('toma_id', sa.BigInteger(),
                  sa.ForeignKey('inventarios_tomas.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('producto_id', sa.BigInteger(),
                  sa.ForeignKey('inventarios_productos.id', ondelete='SET NULL'), nullable=True),
        sa.Column('bodega_id', sa.BigInteger(),
                  sa.ForeignKey('inventarios_bodegas.id', ondelete='SET NULL'), nullable=True),
        sa.Column('codigo', sa.String(50), nullable=True, index=True),
        sa.Column('descripcion', sa.String(255), nullable=False),
        sa.Column('unidad_medida', sa.String(20), nullable=True, server_default='UND'),
        sa.Column('cantidad', sa.Numeric(15, 4), nullable=False),
        sa.Column('costo_unitario', sa.Numeric(15, 4), nullable=False),
        sa.Column('costo_total', sa.Numeric(15, 2), nullable=False),
        sa.Column('bodega_codigo', sa.String(20), nullable=True),
        # AuditableFull
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('created_by', sa.BigInteger(), sa.ForeignKey('public.users.id', ondelete='SET NULL'),
                  nullable=True, index=True, comment='Usuario que creó el registro'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now(), index=True),
        sa.Column('updated_by', sa.BigInteger(), sa.ForeignKey('public.users.id', ondelete='SET NULL'),
                  nullable=True, index=True, comment='Usuario que modificó el registro por última vez'),
    )
    op.create_index('idx_inventarios_items_toma', 'inventarios_items', ['toma_id'])
    op.create_index('idx_inventarios_items_codigo', 'inventarios_items', ['codigo'])

    # ============================================================
    # 5. INVENTARIOS_IMPORTACIONES (Auditoría SIN SoftDelete)
    # ============================================================
    op.create_table(
        'inventarios_importaciones',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column('toma_id', sa.BigInteger(),
                  sa.ForeignKey('inventarios_tomas.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('archivo_original', sa.String(255), nullable=False),
        sa.Column('formato', sa.String(10), nullable=False),
        sa.Column('modo', sa.String(20), nullable=False, server_default='REEMPLAZAR'),
        sa.Column('filas_procesadas', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('filas_validas', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('filas_con_error', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('errores', postgresql.JSONB(), nullable=True),
        # AuditableFull
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('created_by', sa.BigInteger(), sa.ForeignKey('public.users.id', ondelete='SET NULL'),
                  nullable=True, index=True, comment='Usuario que creó el registro'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now(), index=True),
        sa.Column('updated_by', sa.BigInteger(), sa.ForeignKey('public.users.id', ondelete='SET NULL'),
                  nullable=True, index=True, comment='Usuario que modificó el registro por última vez'),
    )
    op.create_index('idx_inventarios_importaciones_toma', 'inventarios_importaciones', ['toma_id'])


def downgrade() -> None:
    # Orden inverso de creación (primero las que tienen FKs a otras)
    op.drop_table('inventarios_importaciones')
    op.drop_table('inventarios_items')
    op.drop_table('inventarios_tomas')
    op.drop_table('inventarios_productos')
    op.drop_table('inventarios_bodegas')