"""create_roles_catalog

Revision ID: e3a55494edc7
Revises: db7f08b62617
Create Date: 2026-05-31 20:23:41.577615

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'e3a55494edc7'
down_revision: Union[str, None] = 'db7f08b62617'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'roles',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('codigo', sa.String(30), unique=True, nullable=False, index=True),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('nivel_acceso', sa.Integer(), nullable=False),
        schema='public'
    )
    
    op.execute("""
        INSERT INTO public.roles (codigo, nombre, descripcion, nivel_acceso) VALUES
        ('superadmin', 'Super Administrador', 'Acceso total al sistema', 100),
        ('tenant_manager', 'Gestor de Firma', 'Administra usuarios y empresas del tenant', 80),
        ('tenant_member', 'Contador/Auxiliar', 'Acceso restringido a empresas asignadas', 60),
        ('tenant_client', 'Cliente Externo', 'Solo lectura de su empresa', 20);
    """)

def downgrade():
    op.execute("DELETE FROM public.roles")
    op.drop_table('roles', schema='public')
