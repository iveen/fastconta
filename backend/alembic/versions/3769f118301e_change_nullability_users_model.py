"""change_nullability_users_model

Revision ID: 3769f118301e
Revises: 9b4ed6096f13
Create Date: 2026-07-07 10:59:56.100670

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3769f118301e'
down_revision: Union[str, None] = '9b4ed6096f13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE public.users 
        SET tenant_id = (SELECT id FROM public.tenants WHERE schema_name = 'system')
        WHERE tenant_id IS NULL;
    """)
    
    # Luego, hacer la columna NOT NULL
    op.alter_column(
        'users', 'tenant_id',
        existing_type=sa.BigInteger(),
        nullable=False,
        schema='public'
    )


def downgrade() -> None:
    op.alter_column(
        'users', 'tenant_id',
        existing_type=sa.BigInteger(),
        nullable=True,
        schema='public'
    )
