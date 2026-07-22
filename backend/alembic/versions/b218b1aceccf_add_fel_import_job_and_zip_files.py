"""add_fel_import_job_and_zip_files

Revision ID: b218b1aceccf
Revises: ca6d8f816b29
Create Date: 2026-07-22 14:10:49.255812
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b218b1aceccf'
down_revision: Union[str, None] = 'ca6d8f816b29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear la tabla fel_import_jobs en el schema public
    op.create_table(
        'fel_import_jobs',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('empresa_id', sa.BigInteger(), nullable=False),
        sa.Column('usuario_id', sa.BigInteger(), nullable=True),
        sa.Column('archivo_original', sa.String(length=255), nullable=False),
        sa.Column('archivo_ruta', sa.String(length=500), nullable=False),
        sa.Column('formato', sa.String(length=10), server_default='ZIP', nullable=False),
        sa.Column('tamano_bytes', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('estado', sa.String(length=20), server_default='PENDIENTE', nullable=False),
        sa.Column('archivos_totales', sa.Integer(), server_default='0', nullable=False),
        sa.Column('archivos_procesados', sa.Integer(), server_default='0', nullable=False),
        sa.Column('facturas_creadas', sa.Integer(), server_default='0', nullable=False),
        sa.Column('facturas_duplicadas', sa.Integer(), server_default='0', nullable=False),
        sa.Column('facturas_con_error', sa.Integer(), server_default='0', nullable=False),
        sa.Column('porcentaje', sa.SmallInteger(), server_default='0', nullable=False),
        sa.Column('errores', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('mensaje_error', sa.Text(), nullable=True),
        sa.Column('notificado', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('notificado_en', sa.DateTime(timezone=True), nullable=True),
        sa.Column('iniciado_en', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finalizado_en', sa.DateTime(timezone=True), nullable=True),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['usuario_id'], ['public.users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_id'),
        schema='public'
    )

    # Crear índices definidos en __table_args__
    op.create_index('idx_fel_jobs_tenant', 'fel_import_jobs', ['tenant_id'], schema='public')
    op.create_index('idx_fel_jobs_empresa', 'fel_import_jobs', ['tenant_id', 'empresa_id'], schema='public')
    op.create_index('idx_fel_jobs_estado', 'fel_import_jobs', ['estado'], schema='public')
    op.create_index('idx_fel_jobs_usuario', 'fel_import_jobs', ['usuario_id'], schema='public')
    op.create_index('idx_fel_jobs_created', 'fel_import_jobs', ['created_at'], schema='public')


def downgrade() -> None:
    # Eliminar índices primero
    op.drop_index('idx_fel_jobs_created', table_name='fel_import_jobs', schema='public')
    op.drop_index('idx_fel_jobs_usuario', table_name='fel_import_jobs', schema='public')
    op.drop_index('idx_fel_jobs_estado', table_name='fel_import_jobs', schema='public')
    op.drop_index('idx_fel_jobs_empresa', table_name='fel_import_jobs', schema='public')
    op.drop_index('idx_fel_jobs_tenant', table_name='fel_import_jobs', schema='public')

    # Eliminar la tabla
    op.drop_table('fel_import_jobs', schema='public')