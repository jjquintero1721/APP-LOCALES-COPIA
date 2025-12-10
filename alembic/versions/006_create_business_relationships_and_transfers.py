"""Create business relationships and transfers tables

Revision ID: 006
Revises: 005
Create Date: 2025-12-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create business_relationships table
    op.create_table(
        'business_relationships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('requester_business_id', sa.Integer(), nullable=False),
        sa.Column('target_business_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'active', 'rejected', name='relationshipstatus'), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['requester_business_id'], ['business.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_business_id'], ['business.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('requester_business_id', 'target_business_id', name='uq_business_relationship')
    )
    op.create_index(op.f('ix_business_relationships_id'), 'business_relationships', ['id'], unique=False)
    op.create_index(op.f('ix_business_relationships_requester_business_id'), 'business_relationships', ['requester_business_id'], unique=False)
    op.create_index(op.f('ix_business_relationships_target_business_id'), 'business_relationships', ['target_business_id'], unique=False)
    op.create_index(op.f('ix_business_relationships_status'), 'business_relationships', ['status'], unique=False)

    # Create inventory_transfers table
    op.create_table(
        'inventory_transfers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_business_id', sa.Integer(), nullable=False),
        sa.Column('to_business_id', sa.Integer(), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'completed', 'cancelled', 'rejected', name='transferstatus'), nullable=False, server_default='pending'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['from_business_id'], ['business.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_business_id'], ['business.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_transfers_id'), 'inventory_transfers', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_transfers_from_business_id'), 'inventory_transfers', ['from_business_id'], unique=False)
    op.create_index(op.f('ix_inventory_transfers_to_business_id'), 'inventory_transfers', ['to_business_id'], unique=False)
    op.create_index(op.f('ix_inventory_transfers_created_by_user_id'), 'inventory_transfers', ['created_by_user_id'], unique=False)
    op.create_index(op.f('ix_inventory_transfers_status'), 'inventory_transfers', ['status'], unique=False)

    # Create transfer_items table
    op.create_table(
        'transfer_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transfer_id', sa.Integer(), nullable=False),
        sa.Column('inventory_item_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(10, 3), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['transfer_id'], ['inventory_transfers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inventory_item_id'], ['inventory_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transfer_id', 'inventory_item_id', name='uq_transfer_item')
    )
    op.create_index(op.f('ix_transfer_items_id'), 'transfer_items', ['id'], unique=False)
    op.create_index(op.f('ix_transfer_items_transfer_id'), 'transfer_items', ['transfer_id'], unique=False)
    op.create_index(op.f('ix_transfer_items_inventory_item_id'), 'transfer_items', ['inventory_item_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_transfer_items_inventory_item_id'), table_name='transfer_items')
    op.drop_index(op.f('ix_transfer_items_transfer_id'), table_name='transfer_items')
    op.drop_index(op.f('ix_transfer_items_id'), table_name='transfer_items')
    op.drop_table('transfer_items')

    op.drop_index(op.f('ix_inventory_transfers_status'), table_name='inventory_transfers')
    op.drop_index(op.f('ix_inventory_transfers_created_by_user_id'), table_name='inventory_transfers')
    op.drop_index(op.f('ix_inventory_transfers_to_business_id'), table_name='inventory_transfers')
    op.drop_index(op.f('ix_inventory_transfers_from_business_id'), table_name='inventory_transfers')
    op.drop_index(op.f('ix_inventory_transfers_id'), table_name='inventory_transfers')
    op.drop_table('inventory_transfers')

    op.drop_index(op.f('ix_business_relationships_status'), table_name='business_relationships')
    op.drop_index(op.f('ix_business_relationships_target_business_id'), table_name='business_relationships')
    op.drop_index(op.f('ix_business_relationships_requester_business_id'), table_name='business_relationships')
    op.drop_index(op.f('ix_business_relationships_id'), table_name='business_relationships')
    op.drop_table('business_relationships')

    op.execute('DROP TYPE transferstatus')
    op.execute('DROP TYPE relationshipstatus')
