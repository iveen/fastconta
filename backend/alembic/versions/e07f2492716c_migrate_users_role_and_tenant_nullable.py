"""migrate_users_role_and_tenant_nullable

Revision ID: e07f2492716c
Revises: e3a55494edc7
Create Date: 2026-05-31 20:26:11.027557

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'e07f2492716c'
down_revision: Union[str, None] = 'e3a55494edc7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. Añadir columna FK
    op.add_column('users', sa.Column('role_id', UUID(as_uuid=True), sa.ForeignKey('public.roles.id')), schema='public')
    
    # 2. Mapear roles legacy (admin->tenant_manager, contador/auxiliar->tenant_member)
    op.execute("""
        UPDATE public.users SET role_id = (
            SELECT id FROM public.roles WHERE codigo = CASE
                WHEN role = 'admin' THEN 'tenant_manager'
                WHEN role IN ('contador', 'auxiliar') THEN 'tenant_member'
                WHEN role = 'superadmin' THEN 'superadmin'
                ELSE 'tenant_member'
            END
        ) WHERE role IS NOT NULL;
    """)
    
    # 3. Hacer tenant_id nullable (para superadmin)
    op.alter_column('users', 'tenant_id', nullable=True, schema='public')
    
    # 4. Forzar NOT NULL en role_id y eliminar columna vieja
    op.alter_column('users', 'role_id', nullable=False, schema='public')
    op.drop_column('users', 'role', schema='public')

def downgrade():
    op.add_column('users', sa.Column('role', sa.String(50)), schema='public')
    op.execute("""
        UPDATE public.users u SET role = r.codigo
        FROM public.roles r WHERE u.role_id = r.id;
    """)
    op.alter_column('users', 'tenant_id', nullable=False, schema='public')
    op.drop_column('users', 'role_id', schema='public')
