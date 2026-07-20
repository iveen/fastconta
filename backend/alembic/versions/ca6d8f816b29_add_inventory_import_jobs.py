"""add_inventory_import_jobs

Revision ID: ca6d8f816b29
Revises: 057ab6f6f99b
Create Date: 2026-07-19 18:40:20.827950

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ca6d8f816b29'
down_revision: Union[str, None] = '057ab6f6f99b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'inventarios_importacion_jobs',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        
        # Identificación tenant/empresa (sin FK)
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('empresa_id', sa.BigInteger(), nullable=False),
        sa.Column('toma_id', sa.BigInteger(), nullable=False),
        sa.Column('usuario_id', sa.BigInteger(), sa.ForeignKey('public.users.id', ondelete='SET NULL'), nullable=True),
        
        # Archivo
        sa.Column('archivo_original', sa.String(255), nullable=False),
        sa.Column('archivo_ruta', sa.String(500), nullable=False),
        sa.Column('formato', sa.String(10), nullable=False),
        sa.Column('tamano_bytes', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('modo', sa.String(20), nullable=False, server_default='REEMPLAZAR'),
        
        # Estado
        sa.Column('estado', sa.String(20), nullable=False, server_default='PENDIENTE'),
        sa.Column('filas_totales', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('filas_procesadas', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('filas_validas', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('filas_con_error', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('porcentaje', sa.SmallInteger(), nullable=False, server_default='0'),
        
        # Resultado (sin FK)
        sa.Column('importacion_id', sa.BigInteger(), nullable=True),
        sa.Column('errores', postgresql.JSONB()),
        sa.Column('mensaje_error', sa.Text()),
        
        # Notificación
        sa.Column('notificado', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notificado_en', sa.DateTime(timezone=True)),
        
        # Control
        sa.Column('iniciado_en', sa.DateTime(timezone=True)),
        sa.Column('finalizado_en', sa.DateTime(timezone=True)),
        sa.Column('locked_at', sa.DateTime(timezone=True)),
        
        # Auditoría
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.BigInteger(), sa.ForeignKey('public.users.id', ondelete='SET NULL')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_by', sa.BigInteger(), sa.ForeignKey('public.users.id', ondelete='SET NULL')),
    )
    
    # Índices
    op.create_index('idx_import_jobs_tenant', 'inventarios_importacion_jobs', ['tenant_id'])
    op.create_index('idx_import_jobs_empresa', 'inventarios_importacion_jobs', ['tenant_id', 'empresa_id'])
    op.create_index('idx_import_jobs_toma', 'inventarios_importacion_jobs', ['toma_id'])
    op.create_index('idx_import_jobs_estado', 'inventarios_importacion_jobs', ['estado'])
    op.create_index('idx_import_jobs_usuario', 'inventarios_importacion_jobs', ['usuario_id'])
    op.create_index('idx_import_jobs_created', 'inventarios_importacion_jobs', ['created_at'])


def downgrade() -> None:
    op.drop_table('inventarios_importacion_jobs')