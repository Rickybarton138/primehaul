"""add missing item columns

Revision ID: fix003
Revises: fix002
Create Date: 2026-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'fix003'
down_revision: Union[str, None] = 'fix002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(conn, table, column):
    result = conn.execute(text(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='{table}' AND column_name='{column}'
    """))
    return result.fetchone() is not None


def upgrade() -> None:
    conn = op.get_bind()

    # Items table - missing packing classification columns
    if not column_exists(conn, 'items', 'item_category'):
        op.add_column('items', sa.Column('item_category', sa.String(50), nullable=True))

    if not column_exists(conn, 'items', 'packing_requirement'):
        op.add_column('items', sa.Column('packing_requirement', sa.String(50), nullable=True))


def downgrade() -> None:
    pass  # Don't remove columns on downgrade
