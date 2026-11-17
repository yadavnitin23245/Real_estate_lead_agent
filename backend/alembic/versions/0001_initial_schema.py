"""initial schema

The embedding column size comes from EMBED_DIM (app config). Changing the
embedding model to one with a different size needs a new migration.

Revision ID: 0001
Revises:
Create Date: 2026-11-12 14:55:18.324759
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from app.config import get_settings

EMBED_DIM = get_settings().embed_dim

revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # init.sql creates it too; repeated here so migrations also work on a non-docker Postgres
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role', sa.Enum('buyer', 'seller', 'sales_agent', 'admin', name='user_role', native_enum=False, create_constraint=True, length=20), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('email', name=op.f('uq_users_email'))
    )
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_table('leads',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('guest_id', sa.String(length=64), nullable=True),
    sa.Column('name', sa.String(length=120), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('email', sa.String(length=254), nullable=True),
    sa.Column('budget_min', sa.BigInteger(), nullable=True),
    sa.Column('budget_max', sa.BigInteger(), nullable=True),
    sa.Column('city', sa.String(length=80), nullable=True),
    sa.Column('preferred_localities', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
    sa.Column('property_type', sa.Enum('apartment', 'house', 'villa', 'plot_land', 'commercial', name='lead_property_type', native_enum=False, create_constraint=True, length=20), nullable=True),
    sa.Column('bedrooms', sa.Integer(), nullable=True),
    sa.Column('timeline_months', sa.Integer(), nullable=True),
    sa.Column('loan_preapproved', sa.Boolean(), nullable=True),
    sa.Column('must_haves', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.Column('soft_preferences', sa.Text(), nullable=True),
    sa.Column('score', sa.Enum('hot', 'warm', 'cold', name='lead_score', native_enum=False, create_constraint=True, length=20), server_default='cold', nullable=False),
    sa.Column('status', sa.Enum('new', 'qualifying', 'handed_off', 'nurture', 'closed', name='lead_status', native_enum=False, create_constraint=True, length=20), server_default='new', nullable=False),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('assigned_agent_id', sa.Integer(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('handed_off_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['assigned_agent_id'], ['users.id'], name=op.f('fk_leads_assigned_agent_id_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_leads_user_id_users'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_leads'))
    )
    op.create_index(op.f('ix_leads_assigned_agent_id'), 'leads', ['assigned_agent_id'], unique=False)
    op.create_index(op.f('ix_leads_guest_id'), 'leads', ['guest_id'], unique=False)
    op.create_index('ix_leads_score_status', 'leads', ['score', 'status'], unique=False)
    op.create_index(op.f('ix_leads_user_id'), 'leads', ['user_id'], unique=False)
    op.create_table('listings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ref_code', sa.String(length=20), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('city', sa.String(length=80), nullable=False),
    sa.Column('locality', sa.String(length=80), nullable=False),
    sa.Column('property_type', sa.Enum('apartment', 'house', 'villa', 'plot_land', 'commercial', name='property_type', native_enum=False, create_constraint=True, length=20), nullable=False),
    sa.Column('bedrooms', sa.Integer(), nullable=True),
    sa.Column('bathrooms', sa.Integer(), nullable=True),
    sa.Column('area_value', sa.Float(), nullable=True),
    sa.Column('area_unit', sa.Enum('sqft', 'sqm', 'sqyd', 'guntha', 'acre', name='area_unit', native_enum=False, create_constraint=True, length=20), server_default='sqft', nullable=False),
    sa.Column('price_inr', sa.BigInteger(), nullable=False),
    sa.Column('furnishing', sa.Enum('unfurnished', 'semi_furnished', 'fully_furnished', name='furnishing', native_enum=False, create_constraint=True, length=20), nullable=True),
    sa.Column('has_parking', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('near_school', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('near_metro', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('status', sa.Enum('available', 'sold', name='listing_status', native_enum=False, create_constraint=True, length=20), server_default='available', nullable=False),
    sa.Column('approval_status', sa.Enum('pending', 'approved', 'rejected', name='approval_status', native_enum=False, create_constraint=True, length=20), server_default='pending', nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('embedding', Vector(EMBED_DIM), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("property_type <> 'plot_land' OR (bedrooms IS NULL AND bathrooms IS NULL AND area_value IS NOT NULL)", name=op.f('ck_listings_plot_shape')),
    sa.CheckConstraint('area_value IS NULL OR area_value > 0', name=op.f('ck_listings_area_positive')),
    sa.CheckConstraint('price_inr > 0', name=op.f('ck_listings_price_positive')),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name=op.f('fk_listings_owner_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_listings')),
    sa.UniqueConstraint('ref_code', name=op.f('uq_listings_ref_code'))
    )
    op.create_index('ix_listings_embedding_hnsw', 'listings', ['embedding'], unique=False, postgresql_using='hnsw', postgresql_ops={'embedding': 'vector_cosine_ops'})
    op.create_index(op.f('ix_listings_locality'), 'listings', ['locality'], unique=False)
    op.create_index(op.f('ix_listings_owner_id'), 'listings', ['owner_id'], unique=False)
    op.create_index(op.f('ix_listings_price_inr'), 'listings', ['price_inr'], unique=False)
    op.create_index('ix_listings_visible', 'listings', ['approval_status', 'status', 'city', 'property_type'], unique=False)
    op.create_table('conversations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lead_id', sa.Integer(), nullable=False),
    sa.Column('thread_id', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], name=op.f('fk_conversations_lead_id_leads'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_conversations')),
    sa.UniqueConstraint('thread_id', name=op.f('uq_conversations_thread_id'))
    )
    op.create_index(op.f('ix_conversations_lead_id'), 'conversations', ['lead_id'], unique=False)
    op.create_table('events',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('lead_id', sa.Integer(), nullable=True),
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('tokens', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('cost', sa.Float(), server_default=sa.text('0'), nullable=False),
    sa.Column('latency_ms', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], name=op.f('fk_events_lead_id_leads'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_events'))
    )
    op.create_index(op.f('ix_events_created_at'), 'events', ['created_at'], unique=False)
    op.create_index(op.f('ix_events_lead_id'), 'events', ['lead_id'], unique=False)
    op.create_index(op.f('ix_events_type'), 'events', ['type'], unique=False)
    op.create_table('lead_matches',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lead_id', sa.Integer(), nullable=False),
    sa.Column('listing_id', sa.Integer(), nullable=False),
    sa.Column('rank', sa.Integer(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('matched_filters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], name=op.f('fk_lead_matches_lead_id_leads'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['listing_id'], ['listings.id'], name=op.f('fk_lead_matches_listing_id_listings'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_lead_matches')),
    sa.UniqueConstraint('lead_id', 'listing_id', name='uq_lead_matches_lead_listing')
    )
    op.create_index(op.f('ix_lead_matches_lead_id'), 'lead_matches', ['lead_id'], unique=False)
    op.create_table('listing_images',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('listing_id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(length=500), nullable=False),
    sa.Column('thumb_url', sa.String(length=500), nullable=False),
    sa.Column('storage_key', sa.String(length=300), nullable=False),
    sa.Column('sort_order', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['listing_id'], ['listings.id'], name=op.f('fk_listing_images_listing_id_listings'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_listing_images'))
    )
    op.create_index(op.f('ix_listing_images_listing_id'), 'listing_images', ['listing_id'], unique=False)
    op.create_table('shortlists',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('listing_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['listing_id'], ['listings.id'], name=op.f('fk_shortlists_listing_id_listings'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_shortlists_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'listing_id', name=op.f('pk_shortlists'))
    )
    op.create_table('visit_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lead_id', sa.Integer(), nullable=False),
    sa.Column('listing_id', sa.Integer(), nullable=False),
    sa.Column('preferred_time', sa.String(length=120), nullable=False),
    sa.Column('status', sa.Enum('requested', 'confirmed', 'completed', 'cancelled', name='visit_status', native_enum=False, create_constraint=True, length=20), server_default='requested', nullable=False),
    sa.Column('assigned_agent_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['assigned_agent_id'], ['users.id'], name=op.f('fk_visit_requests_assigned_agent_id_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], name=op.f('fk_visit_requests_lead_id_leads'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['listing_id'], ['listings.id'], name=op.f('fk_visit_requests_listing_id_listings'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_visit_requests'))
    )
    op.create_index(op.f('ix_visit_requests_assigned_agent_id'), 'visit_requests', ['assigned_agent_id'], unique=False)
    op.create_index(op.f('ix_visit_requests_lead_id'), 'visit_requests', ['lead_id'], unique=False)
    op.create_table('messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('conversation_id', sa.Integer(), nullable=False),
    sa.Column('lead_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.Enum('user', 'assistant', name='message_role', native_enum=False, create_constraint=True, length=20), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], name=op.f('fk_messages_conversation_id_conversations'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], name=op.f('fk_messages_lead_id_leads'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_messages'))
    )
    op.create_index(op.f('ix_messages_conversation_id'), 'messages', ['conversation_id'], unique=False)
    op.create_index('ix_messages_lead_created', 'messages', ['lead_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_messages_lead_created', table_name='messages')
    op.drop_index(op.f('ix_messages_conversation_id'), table_name='messages')
    op.drop_table('messages')
    op.drop_index(op.f('ix_visit_requests_lead_id'), table_name='visit_requests')
    op.drop_index(op.f('ix_visit_requests_assigned_agent_id'), table_name='visit_requests')
    op.drop_table('visit_requests')
    op.drop_table('shortlists')
    op.drop_index(op.f('ix_listing_images_listing_id'), table_name='listing_images')
    op.drop_table('listing_images')
    op.drop_index(op.f('ix_lead_matches_lead_id'), table_name='lead_matches')
    op.drop_table('lead_matches')
    op.drop_index(op.f('ix_events_type'), table_name='events')
    op.drop_index(op.f('ix_events_lead_id'), table_name='events')
    op.drop_index(op.f('ix_events_created_at'), table_name='events')
    op.drop_table('events')
    op.drop_index(op.f('ix_conversations_lead_id'), table_name='conversations')
    op.drop_table('conversations')
    op.drop_index('ix_listings_visible', table_name='listings')
    op.drop_index(op.f('ix_listings_price_inr'), table_name='listings')
    op.drop_index(op.f('ix_listings_owner_id'), table_name='listings')
    op.drop_index(op.f('ix_listings_locality'), table_name='listings')
    op.drop_index('ix_listings_embedding_hnsw', table_name='listings', postgresql_using='hnsw', postgresql_ops={'embedding': 'vector_cosine_ops'})
    op.drop_table('listings')
    op.drop_index(op.f('ix_leads_user_id'), table_name='leads')
    op.drop_index('ix_leads_score_status', table_name='leads')
    op.drop_index(op.f('ix_leads_guest_id'), table_name='leads')
    op.drop_index(op.f('ix_leads_assigned_agent_id'), table_name='leads')
    op.drop_table('leads')
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_table('users')
