"""add_campos_auditoria_empresa

Revision ID: 36c4b2fdaa6d
Revises: c68742719394
Create Date: 2026-07-02 07:40:55.747835

Agrega campos de auditoría (AuditableFull) a las tablas:
- empresas
- domicilios
- representantes_legales

Campos agregados:
- created_at (DateTime, NOT NULL, index)
- created_by (UUID, FK public.users.id, nullable, index)
- updated_at (DateTime, nullable, index)
- updated_by (UUID, FK public.users.id, nullable, index)

Nota: empresas y representantes_legales ya tenían created_at,
por lo que solo se agregan los 3 campos restantes.
"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '36c4b2fdaa6d'
down_revision: Union[str, None] = 'c68742719394'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    # ============================================================
    # TABLA: empresas
    # ============================================================
    # created_at ya existe, solo agregamos los 3 campos faltantes
    op.add_column('empresas',
        sa.Column('created_by', sa.dialects.postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('public.users.id', ondelete='SET NULL'),
                  nullable=True, index=True,
                  comment='Usuario que creó el registro')
    )
    op.add_column('empresas',
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  nullable=True, index=True,
                  server_default=sa.text('now()'))
    )
    op.add_column('empresas',
        sa.Column('updated_by', sa.dialects.postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('public.users.id', ondelete='SET NULL'),
                  nullable=True, index=True,
                  comment='Usuario que modificó el registro por última vez')
    )
    op.alter_column('empresas', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text('now()')
    )
    op.create_index('ix_empresas_created_at', 'empresas', ['created_at'])


    # ============================================================
    # TABLA: domicilios
    # ============================================================
    # No tiene created_at, agregamos los 4 campos
    op.add_column('domicilios',
        sa.Column('created_at', sa.DateTime(timezone=True),
                  nullable=False, index=True,
                  server_default=sa.text('now()'))
    )
    op.add_column('domicilios',
        sa.Column('created_by', sa.dialects.postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('public.users.id', ondelete='SET NULL'),
                  nullable=True, index=True,
                  comment='Usuario que creó el registro')
    )
    op.add_column('domicilios',
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  nullable=True, index=True,
                  server_default=sa.text('now()'))
    )
    op.add_column('domicilios',
        sa.Column('updated_by', sa.dialects.postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('public.users.id', ondelete='SET NULL'),
                  nullable=True, index=True,
                  comment='Usuario que modificó el registro por última vez')
    )

    # ============================================================
    # TABLA: representantes_legales
    # ============================================================
    # created_at ya existe, solo agregamos los 3 campos faltantes
    op.add_column('representantes_legales',
        sa.Column('created_by', sa.dialects.postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('public.users.id', ondelete='SET NULL'),
                  nullable=True, index=True,
                  comment='Usuario que creó el registro')
    )
    op.add_column('representantes_legales',
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  nullable=True, index=True,
                  server_default=sa.text('now()'))
    )
    op.add_column('representantes_legales',
        sa.Column('updated_by', sa.dialects.postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('public.users.id', ondelete='SET NULL'),
                  nullable=True, index=True,
                  comment='Usuario que modificó el registro por última vez')
    )


def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    # ============================================================
    # TABLA: representantes_legales
    # ============================================================
    op.drop_column('representantes_legales', 'updated_by')
    op.drop_column('representantes_legales', 'updated_at')
    op.drop_column('representantes_legales', 'created_by')
    # created_at NO se elimina porque ya existía antes

    # ============================================================
    # TABLA: domicilios
    # ============================================================
    op.drop_column('domicilios', 'updated_by')
    op.drop_column('domicilios', 'updated_at')
    op.drop_column('domicilios', 'created_by')
    op.drop_column('domicilios', 'created_at')

    # ============================================================
    # TABLA: empresas
    # ============================================================
    op.drop_column('empresas', 'updated_by')
    op.drop_column('empresas', 'updated_at')
    op.drop_column('empresas', 'created_by')
    # created_at NO se elimina porque ya existía antes