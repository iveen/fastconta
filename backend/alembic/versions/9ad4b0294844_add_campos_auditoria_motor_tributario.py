"""add_campos_auditoria_motor_tributario

Revision ID: 9ad4b0294844
Revises: 3d672b42eb14
Create Date: 2026-07-02 08:35:27.544024

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by alembic.
revision: str = '9ad4b0294844'
down_revision: Union[str, None] = '3d672b42eb14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = 'public'

# Tablas que reciben los 4 campos de auditoría (ninguno existía antes)
TABLAS_COMPLETAS = ['regimenes_fiscales', 'regimen_dte_config']

# Tabla que ya tenía created_at/updated_at → solo agrega *_by
TABLAS_PARCIALES = ['tipos_dte']


def _add_audit_columns(table: str, include_timestamps: bool) -> None:
    """Agrega columnas del mixin AuditableFull + sus índices."""
    
    # Obtener conexión para inspeccionar esquema
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Obtener columnas existentes de la tabla
    existing_columns = {col['name'] for col in inspector.get_columns(table, schema=SCHEMA)}
    
    if include_timestamps:
        # created_at: verificar si ya existe
        if 'created_at' not in existing_columns:
            op.add_column(
                table,
                sa.Column(
                    'created_at',
                    sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    nullable=False,
                ),
                schema=SCHEMA,
            )
        op.create_index(
            f'ix_{table}_created_at', table, ['created_at'], schema=SCHEMA
        )
        
        # updated_at: verificar si ya existe
        if 'updated_at' not in existing_columns:
            op.add_column(
                table,
                sa.Column(
                    'updated_at',
                    sa.DateTime(timezone=True),
                    nullable=True,
                ),
                schema=SCHEMA,
            )
        op.create_index(
            f'ix_{table}_updated_at', table, ['updated_at'], schema=SCHEMA
        )

    # created_by / updated_by: siempre verificar antes de agregar
    if 'created_by' not in existing_columns:
        op.add_column(
            table,
            sa.Column(
                'created_by',
                UUID(as_uuid=True),
                sa.ForeignKey(f'{SCHEMA}.users.id', ondelete='SET NULL'),
                nullable=True,
                comment='Usuario que creó el registro',
            ),
            schema=SCHEMA,
        )
        op.create_index(
            f'ix_{table}_created_by', table, ['created_by'], schema=SCHEMA
        )
    
    if 'updated_by' not in existing_columns:
        op.add_column(
            table,
            sa.Column(
                'updated_by',
                UUID(as_uuid=True),
                sa.ForeignKey(f'{SCHEMA}.users.id', ondelete='SET NULL'),
                nullable=True,
                comment='Usuario que modificó el registro por última vez',
            ),
            schema=SCHEMA,
        )
        op.create_index(
            f'ix_{table}_updated_by', table, ['updated_by'], schema=SCHEMA
        )

def _drop_audit_columns(table: str, include_timestamps: bool) -> None:
    """Rollback: elimina columnas e índices del mixin."""
    op.drop_index(f'ix_{table}_updated_by', table_name=table, schema=SCHEMA)
    op.drop_index(f'ix_{table}_created_by', table_name=table, schema=SCHEMA)
    op.drop_column(table, 'updated_by', schema=SCHEMA)
    op.drop_column(table, 'created_by', schema=SCHEMA)

    if include_timestamps:
        op.drop_index(f'ix_{table}_updated_at', table_name=table, schema=SCHEMA)
        op.drop_index(f'ix_{table}_created_at', table_name=table, schema=SCHEMA)
        op.drop_column(table, 'updated_at', schema=SCHEMA)
        op.drop_column(table, 'created_at', schema=SCHEMA)


def upgrade() -> None:
    # 1. RegimenFiscal y RegimenDteConfig → 4 campos nuevos
    for tabla in TABLAS_COMPLETAS:
        _add_audit_columns(tabla, include_timestamps=True)

    # 2. TipoDTE → ya tiene created_at/updated_at, solo agrega *_by
    for tabla in TABLAS_PARCIALES:
        _add_audit_columns(tabla, include_timestamps=False)


def downgrade() -> None:
    for tabla in TABLAS_PARCIALES:
        _drop_audit_columns(tabla, include_timestamps=False)

    for tabla in TABLAS_COMPLETAS:
        _drop_audit_columns(tabla, include_timestamps=True)