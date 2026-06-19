"""add_is_active_to_regimenes

Revision ID: 342af5a7af9b
Revises: 3f6a91a9cedf
Create Date: 2026-06-18 20:39:31.977305

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '342af5a7af9b'
down_revision: Union[str, None] = '3f6a91a9cedf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
