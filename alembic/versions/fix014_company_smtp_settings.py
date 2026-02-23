"""Add SMTP settings columns to companies

Revision ID: fix014
Revises: fix013
Create Date: 2026-02-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = 'fix014'
down_revision = 'fix013'
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
    if not column_exists(conn, 'companies', 'smtp_host'):
        op.add_column('companies', sa.Column('smtp_host', sa.String(255)))
    if not column_exists(conn, 'companies', 'smtp_port'):
        op.add_column('companies', sa.Column('smtp_port', sa.Integer()))
    if not column_exists(conn, 'companies', 'smtp_username'):
        op.add_column('companies', sa.Column('smtp_username', sa.String(255)))
    if not column_exists(conn, 'companies', 'smtp_password'):
        op.add_column('companies', sa.Column('smtp_password', sa.String(500)))
    if not column_exists(conn, 'companies', 'smtp_from_email'):
        op.add_column('companies', sa.Column('smtp_from_email', sa.String(255)))


def downgrade():
    conn = op.get_bind()
    for col in ['smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'smtp_from_email']:
        if column_exists(conn, 'companies', col):
            op.drop_column('companies', col)
