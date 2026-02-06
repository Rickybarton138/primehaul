"""Add prepaid credits system

Revision ID: fix008
Revises: fix007
Create Date: 2026-02-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision = 'fix008'
down_revision = 'fix007'
branch_labels = None
depends_on = None


def column_exists(conn, table, column):
    result = conn.execute(text(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='{table}' AND column_name='{column}'
    """))
    return result.fetchone() is not None


def upgrade():
    conn = op.get_bind()

    # Add credits column (default 3 for new signups)
    if not column_exists(conn, 'companies', 'credits'):
        op.add_column('companies', sa.Column('credits', sa.Integer(), server_default='3', nullable=True))

    # Migrate existing companies: credits = free_surveys_remaining (what they have left)
    # For companies that already used surveys, give them their remaining free surveys as credits
    conn.execute(text("""
        UPDATE companies
        SET credits = COALESCE(free_surveys_remaining, 3)
        WHERE credits IS NULL OR credits = 0
    """))


def downgrade():
    conn = op.get_bind()
    if column_exists(conn, 'companies', 'credits'):
        op.drop_column('companies', 'credits')
