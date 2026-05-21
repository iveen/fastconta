"""add_nit_plan_to_tenants_and_registration_attempts

Revision ID: 66a2697e7db8
Revises: 0c22c15aa3d8
Create Date: 2026-05-20 09:20:30.833402

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '66a2697e7db8'
down_revision: Union[str, None] = '0c22c15aa3d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. Añadir columnas como nullable
    op.add_column('tenants', sa.Column('nit', sa.String(15), nullable=True))
    op.add_column('tenants', sa.Column('plan', sa.String(20), server_default='freemium', nullable=True))
    op.add_column('tenants', sa.Column('max_empresas', sa.Integer(), server_default='5', nullable=True))

    # 2. Rellenar registros existentes con un NIT temporal
    op.execute("UPDATE public.tenants SET nit = '0000000-0' WHERE nit IS NULL")
    op.execute("UPDATE public.tenants SET plan = 'freemium' WHERE plan IS NULL")
    op.execute("UPDATE public.tenants SET max_empresas = 5 WHERE max_empresas IS NULL")

    # 3. Ahora sí aplicar NOT NULL y UNIQUE
    op.alter_column('tenants', 'nit', nullable=False)
    op.alter_column('tenants', 'plan', nullable=False)
    op.alter_column('tenants', 'max_empresas', nullable=False)
    op.create_unique_constraint('uq_tenants_nit', 'tenants', ['nit'])

    # 4. Crear tabla registration_attempts
    op.create_table(
        'registration_attempts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table('registration_attempts')
    op.drop_constraint('uq_tenants_nit', 'tenants')
    op.drop_column('tenants', 'max_empresas')
    op.drop_column('tenants', 'plan')
    op.drop_column('tenants', 'nit')