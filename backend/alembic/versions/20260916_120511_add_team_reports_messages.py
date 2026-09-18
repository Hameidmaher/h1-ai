"""Add team_members, messages, reports, assignments tables.

Revision ID: 1789549511
Revises: 
Create Date: 2026-09-16T09:05:11
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "1789549511"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ═══ TEAM MEMBERS ═══
    op.create_table(
        'team_members',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('name_ar', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(20), unique=True, nullable=False, index=True),
        sa.Column('email', sa.String(120), nullable=True, unique=True),
        sa.Column('role', sa.String(30), nullable=False, server_default='pharmacist'),
        sa.Column('specialties', sa.JSON, nullable=True),
        sa.Column('shift', sa.String(20), nullable=False, server_default='morning'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='1', index=True),
        sa.Column('is_available', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('max_concurrent', sa.Integer, nullable=False, server_default='10'),
        sa.Column('current_load', sa.Integer, nullable=False, server_default='0'),
        sa.Column('languages', sa.JSON, nullable=True),
        sa.Column('whatsapp_enabled', sa.Boolean, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_team_role_active', 'team_members', ['role', 'is_active'])
    op.create_index('idx_team_shift_active', 'team_members', ['shift', 'is_active'])
    op.create_index('idx_team_load', 'team_members', ['current_load', 'is_available'])

    # ═══ MESSAGES ═══
    op.create_table(
        'messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('whatsapp_id', sa.String(100), unique=True, nullable=True, index=True),
        sa.Column('from_phone', sa.String(20), nullable=False, index=True),
        sa.Column('from_name', sa.String(100), nullable=True),
        sa.Column('to_phone', sa.String(20), nullable=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('media_url', sa.String(500), nullable=True),
        sa.Column('media_type', sa.String(30), nullable=True),
        sa.Column('direction', sa.String(10), nullable=False, server_default='inbound'),
        sa.Column('classification', sa.String(30), nullable=True, index=True),
        sa.Column('priority', sa.String(20), server_default='normal', index=True),
        sa.Column('processed', sa.Boolean, nullable=False, server_default='0', index=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('chatbot_response', sa.Text, nullable=True),
        sa.Column('handler', sa.String(50), nullable=True),
        sa.Column('meta_data', sa.JSON, nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_message_from_date', 'messages', ['from_phone', 'received_at'])
    op.create_index('idx_message_class_priority', 'messages', ['classification', 'priority'])
    op.create_index('idx_message_processed', 'messages', ['processed', 'received_at'])

    # ═══ REPORTS ═══
    op.create_table(
        'reports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('message_id', sa.String(36), sa.ForeignKey('messages.id'), nullable=False, index=True),
        sa.Column('type', sa.String(50), nullable=False, index=True),
        sa.Column('category', sa.String(50), nullable=True, index=True),
        sa.Column('priority', sa.String(20), nullable=False, server_default='normal', index=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('content', sa.JSON, nullable=False),
        sa.Column('assigned_to', sa.String(36), sa.ForeignKey('team_members.id'), nullable=True, index=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending', index=True),
        sa.Column('sla_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalation_reason', sa.String(200), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_notes', sa.Text, nullable=True),
        sa.Column('resolved_by', sa.String(36), nullable=True),
        sa.Column('response_time_seconds', sa.String(20), nullable=True),
        sa.Column('resolution_time_seconds', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_report_status_priority', 'reports', ['status', 'priority'])
    op.create_index('idx_report_assigned_status', 'reports', ['assigned_to', 'status'])
    op.create_index('idx_report_type_status', 'reports', ['type', 'status'])

    # ═══ ASSIGNMENTS ═══
    op.create_table(
        'assignments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('report_id', sa.String(36), sa.ForeignKey('reports.id'), nullable=False, index=True),
        sa.Column('team_member_id', sa.String(36), sa.ForeignKey('team_members.id'), nullable=False, index=True),
        sa.Column('assigned_by', sa.String(36), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('sla_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('priority_score', sa.Integer, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='assigned', index=True),
        sa.Column('escalated', sa.String(10), server_default='false'),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('action_taken', sa.Text, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('meta_data', sa.JSON, nullable=True),
    )
    op.create_index('idx_assignment_member_status', 'assignments', ['team_member_id', 'status'])
    op.create_index('idx_assignment_report', 'assignments', ['report_id'])
    op.create_index('idx_assignment_sla', 'assignments', ['sla_deadline', 'status'])


def downgrade() -> None:
    op.drop_table('assignments')
    op.drop_table('reports')
    op.drop_table('messages')
    op.drop_table('team_members')
