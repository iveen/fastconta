"""merge_tenant_heads

Revision ID: 75ecd82b4a06
Revises: d879be7df70d, edd37f111c10
Create Date: 2026-06-11 10:24:38.366238

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75ecd82b4a06'
down_revision: Union[str, None] = ('d879be7df70d', 'edd37f111c10')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
