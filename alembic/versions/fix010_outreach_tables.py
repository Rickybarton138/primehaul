"""Add outreach/sales automation tables

Revision ID: fix010_outreach
Revises: fix009_final_quote_price
Create Date: 2026-02-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'fix010_outreach'
down_revision = 'fix009_final_quote_price'
branch_labels = None
depends_on = None


def upgrade():
    # Create outreach_leads table
    op.create_table(
        'outreach_leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('phone', sa.String(50)),
        sa.Column('website', sa.String(255)),
        sa.Column('location', sa.String(100)),
        sa.Column('source', sa.String(50)),
        sa.Column('status', sa.String(20), default='new'),
        sa.Column('emails_sent', sa.Integer, default=0),
        sa.Column('last_contacted', sa.DateTime),
        sa.Column('last_reply', sa.DateTime),
        sa.Column('next_followup', sa.DateTime),
        sa.Column('notes', sa.Text),
        sa.Column('reply_summary', sa.Text),
        sa.Column('sentiment', sa.String(20)),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
    )

    # Create outreach_emails table
    op.create_table(
        'outreach_emails',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('direction', sa.String(10)),  # sent, received
        sa.Column('subject', sa.String(255)),
        sa.Column('body', sa.Text),
        sa.Column('sent_at', sa.DateTime, default=sa.func.now()),
        sa.Column('message_id', sa.String(255)),
    )

    # Create indexes
    op.create_index('ix_outreach_leads_status', 'outreach_leads', ['status'])
    op.create_index('ix_outreach_leads_email', 'outreach_leads', ['email'])
    op.create_index('ix_outreach_emails_lead_id', 'outreach_emails', ['lead_id'])


def downgrade():
    op.drop_index('ix_outreach_emails_lead_id')
    op.drop_index('ix_outreach_leads_email')
    op.drop_index('ix_outreach_leads_status')
    op.drop_table('outreach_emails')
    op.drop_table('outreach_leads')
