"""Add Stripe Connect and usage tracking fields to companies

Revision ID: fix005
Revises: fix004_bulky_weight_threshold
Create Date: 2026-02-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix005'
down_revision = 'fix004_bulky_weight_threshold'
branch_labels = None
depends_on = None


def upgrade():
    # Add Stripe Connect fields for direct deposit payments
    op.add_column('companies', sa.Column('stripe_connect_account_id', sa.String(255), nullable=True))
    op.add_column('companies', sa.Column('stripe_connect_onboarding_complete', sa.Boolean(), server_default='false', nullable=True))

    # Add usage tracking for pay-per-survey billing
    op.add_column('companies', sa.Column('surveys_used', sa.Integer(), server_default='0', nullable=True))
    op.add_column('companies', sa.Column('free_surveys_remaining', sa.Integer(), server_default='3', nullable=True))

    # Create indexes
    op.create_index('idx_companies_stripe_connect', 'companies', ['stripe_connect_account_id'], unique=True)


def downgrade():
    op.drop_index('idx_companies_stripe_connect', table_name='companies')
    op.drop_column('companies', 'free_surveys_remaining')
    op.drop_column('companies', 'surveys_used')
    op.drop_column('companies', 'stripe_connect_onboarding_complete')
    op.drop_column('companies', 'stripe_connect_account_id')
