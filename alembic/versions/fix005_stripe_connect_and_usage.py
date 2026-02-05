"""Add Stripe Connect and usage tracking fields to companies

Revision ID: fix005
Revises: fix004
Create Date: 2026-02-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'fix005'
down_revision = 'fix004'
branch_labels = None
depends_on = None


def column_exists(conn, table, column):
    result = conn.execute(text(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='{table}' AND column_name='{column}'
    """))
    return result.fetchone() is not None


def index_exists(conn, index_name):
    result = conn.execute(text(f"""
        SELECT indexname FROM pg_indexes
        WHERE indexname='{index_name}'
    """))
    return result.fetchone() is not None


def upgrade():
    conn = op.get_bind()

    # Add Stripe Connect fields for direct deposit payments
    if not column_exists(conn, 'companies', 'stripe_connect_account_id'):
        op.add_column('companies', sa.Column('stripe_connect_account_id', sa.String(255), nullable=True))

    if not column_exists(conn, 'companies', 'stripe_connect_onboarding_complete'):
        op.add_column('companies', sa.Column('stripe_connect_onboarding_complete', sa.Boolean(), server_default='false', nullable=True))

    # Add usage tracking for pay-per-survey billing
    if not column_exists(conn, 'companies', 'surveys_used'):
        op.add_column('companies', sa.Column('surveys_used', sa.Integer(), server_default='0', nullable=True))

    if not column_exists(conn, 'companies', 'free_surveys_remaining'):
        op.add_column('companies', sa.Column('free_surveys_remaining', sa.Integer(), server_default='3', nullable=True))

    # Create indexes
    if not index_exists(conn, 'idx_companies_stripe_connect'):
        op.create_index('idx_companies_stripe_connect', 'companies', ['stripe_connect_account_id'], unique=True)


def downgrade():
    conn = op.get_bind()
    if index_exists(conn, 'idx_companies_stripe_connect'):
        op.drop_index('idx_companies_stripe_connect', table_name='companies')
    if column_exists(conn, 'companies', 'free_surveys_remaining'):
        op.drop_column('companies', 'free_surveys_remaining')
    if column_exists(conn, 'companies', 'surveys_used'):
        op.drop_column('companies', 'surveys_used')
    if column_exists(conn, 'companies', 'stripe_connect_onboarding_complete'):
        op.drop_column('companies', 'stripe_connect_onboarding_complete')
    if column_exists(conn, 'companies', 'stripe_connect_account_id'):
        op.drop_column('companies', 'stripe_connect_account_id')
