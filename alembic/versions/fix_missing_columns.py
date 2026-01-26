"""fix_missing_columns

Revision ID: fix001
Revises: 1c9ab1b72be0
Create Date: 2026-01-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'fix001'
down_revision: Union[str, None] = '1c9ab1b72be0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns if they don't exist
    conn = op.get_bind()

    # Check and add customer_provides_packing
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='jobs' AND column_name='customer_provides_packing'
    """))
    if result.fetchone() is None:
        op.add_column('jobs', sa.Column('customer_provides_packing', sa.Boolean(), nullable=True, server_default='false'))

    # Check and add packing_labor_hours
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='jobs' AND column_name='packing_labor_hours'
    """))
    if result.fetchone() is None:
        op.add_column('jobs', sa.Column('packing_labor_hours', sa.Float(), nullable=True, server_default='0'))

    # Check and add packing_labor_cost
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='jobs' AND column_name='packing_labor_cost'
    """))
    if result.fetchone() is None:
        op.add_column('jobs', sa.Column('packing_labor_cost', sa.Float(), nullable=True, server_default='0'))


def downgrade() -> None:
    pass  # Don't remove columns on downgrade
