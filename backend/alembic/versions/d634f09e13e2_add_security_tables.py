"""add_security_tables

Revision ID: d634f09e13e2
Revises: c7c654a11c2f
Create Date: 2025-09-27 23:35:21.736602

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'd634f09e13e2'
down_revision = 'c7c654a11c2f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get connection and inspector
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Only create audit_logs if it doesn't exist
    if 'audit_logs' not in existing_tables:
        op.create_table('audit_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('user_email', sa.String(), nullable=True),
            sa.Column('action', sa.String(), nullable=False),
            sa.Column('resource_type', sa.String(), nullable=True),
            sa.Column('resource_id', sa.String(), nullable=True),
            sa.Column('details', sa.JSON(), nullable=True),
            sa.Column('input_data', sa.JSON(), nullable=True),
            sa.Column('output_data', sa.JSON(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('ip_address', sa.String(), nullable=True),
            sa.Column('user_agent', sa.String(), nullable=True),
            sa.Column('endpoint', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
        op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
        op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    
    # Only create user_consents if it doesn't exist
    if 'user_consents' not in existing_tables:
        op.create_table('user_consents',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('action_type', sa.String(), nullable=False),
            sa.Column('scope', sa.String(), nullable=True),
            sa.Column('is_granted', sa.Boolean(), nullable=False),
            sa.Column('conditions', sa.JSON(), nullable=True),
            sa.Column('granted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('use_count', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_user_consents_action_type'), 'user_consents', ['action_type'], unique=False)
        op.create_index(op.f('ix_user_consents_user_id'), 'user_consents', ['user_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_user_consents_user_id'), table_name='user_consents')
    op.drop_index(op.f('ix_user_consents_action_type'), table_name='user_consents')
    op.drop_table('user_consents')
    
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')