"""Add conversation tables

Revision ID: 003
Revises: 002
Create Date: 2025-07-01 09:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create conversation_logs table
    op.create_table('conversation_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=True),
    sa.Column('user_message', sa.Text(), nullable=False),
    sa.Column('intent', sa.String(), nullable=False),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('entities', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('reasoning', sa.Text(), nullable=True),
    sa.Column('fallback_used', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('processing_time_ms', sa.Float(), nullable=True),
    sa.Column('conversation_turn', sa.Integer(), nullable=False, server_default='1'),
    sa.Column('previous_intent', sa.String(), nullable=True),
    sa.Column('user_context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_logs_id'), 'conversation_logs', ['id'], unique=False)
    op.create_index('ix_conversation_logs_user_created', 'conversation_logs', ['user_id', sa.text('created_at DESC')], unique=False)
    op.create_index('ix_conversation_logs_session_turn', 'conversation_logs', ['session_id', 'conversation_turn'], unique=False)
    op.create_index('ix_conversation_logs_intent_confidence', 'conversation_logs', ['intent', sa.text('confidence DESC')], unique=False)
    op.create_index('ix_conversation_logs_fallback', 'conversation_logs', ['fallback_used', sa.text('created_at DESC')], unique=False)
    
    # Create conversation_sessions table
    op.create_table('conversation_sessions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('session_type', sa.String(), nullable=False, server_default='chat'),
    sa.Column('status', sa.String(), nullable=False, server_default='active'),
    sa.Column('current_intent', sa.String(), nullable=True),
    sa.Column('incomplete_entities', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('context_data', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('turn_count', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('successful_intents', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('failed_intents', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('avg_confidence', sa.Float(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=False),
    sa.Column('last_activity', sa.DateTime(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_sessions_id'), 'conversation_sessions', ['id'], unique=False)
    op.create_index('ix_conversation_sessions_user_activity', 'conversation_sessions', ['user_id', sa.text('last_activity DESC')], unique=False)
    op.create_index('ix_conversation_sessions_status_created', 'conversation_sessions', ['status', sa.text('started_at DESC')], unique=False)
    op.create_index('ix_conversation_sessions_type_user', 'conversation_sessions', ['session_type', 'user_id'], unique=False)
    
    # Create intent_feedback table
    op.create_table('intent_feedback',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('conversation_log_id', sa.Integer(), nullable=False),
    sa.Column('original_intent', sa.String(), nullable=False),
    sa.Column('original_confidence', sa.Float(), nullable=False),
    sa.Column('original_entities', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('corrected_intent', sa.String(), nullable=False),
    sa.Column('corrected_entities', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('feedback_type', sa.String(), nullable=False),
    sa.Column('user_comment', sa.Text(), nullable=True),
    sa.Column('feedback_quality', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['conversation_log_id'], ['conversation_logs.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_intent_feedback_id'), 'intent_feedback', ['id'], unique=False)
    op.create_index('ix_intent_feedback_user_created', 'intent_feedback', ['user_id', sa.text('created_at DESC')], unique=False)
    op.create_index('ix_intent_feedback_original_intent', 'intent_feedback', ['original_intent', 'feedback_type'], unique=False)
    op.create_index('ix_intent_feedback_quality', 'intent_feedback', ['feedback_quality', sa.text('created_at DESC')], unique=False)


def downgrade() -> None:
    op.drop_table('intent_feedback')
    op.drop_table('conversation_sessions')
    op.drop_table('conversation_logs')