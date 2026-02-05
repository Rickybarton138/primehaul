"""Add partner account fields to companies

Revision ID: fix006
Revises: fix005
Create Date: 2026-02-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'fix006'
down_revision = 'fix005'
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

    # Add partner flag for unlimited free surveys
    if not column_exists(conn, 'companies', 'is_partner'):
        op.add_column('companies', sa.Column('is_partner', sa.Boolean(), server_default='false', nullable=True))

    if not column_exists(conn, 'companies', 'partner_name'):
        op.add_column('companies', sa.Column('partner_name', sa.String(100), nullable=True))


def downgrade():
    conn = op.get_bind()
    if column_exists(conn, 'companies', 'partner_name'):
        op.drop_column('companies', 'partner_name')
    if column_exists(conn, 'companies', 'is_partner'):
        op.drop_column('companies', 'is_partner')
