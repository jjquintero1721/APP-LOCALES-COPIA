"""Create modifiers tables (groups, modifiers, inventory items, product modifiers)

Revision ID: 008
Revises: 007
Create Date: 2025-12-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create modifier_groups table
    op.create_table(
        'modifier_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('allow_multiple', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['business_id'], ['business.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_modifier_groups_id'), 'modifier_groups', ['id'], unique=False)
    op.create_index(op.f('ix_modifier_groups_business_id'), 'modifier_groups', ['business_id'], unique=False)

    # Create modifiers table
    op.create_table(
        'modifiers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('modifier_group_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price_extra', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['modifier_group_id'], ['modifier_groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('modifier_group_id', 'name', name='uq_modifier_name_per_group'),
        sa.CheckConstraint('price_extra >= 0', name='check_price_extra_non_negative')
    )
    op.create_index(op.f('ix_modifiers_id'), 'modifiers', ['id'], unique=False)
    op.create_index(op.f('ix_modifiers_modifier_group_id'), 'modifiers', ['modifier_group_id'], unique=False)

    # Create modifier_inventory_items table
    op.create_table(
        'modifier_inventory_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('modifier_id', sa.Integer(), nullable=False),
        sa.Column('inventory_item_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(10, 3), nullable=False),
        sa.ForeignKeyConstraint(['modifier_id'], ['modifiers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inventory_item_id'], ['inventory_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('modifier_id', 'inventory_item_id', name='uq_modifier_inventory_item'),
        sa.CheckConstraint('quantity != 0', name='check_quantity_not_zero')
    )
    op.create_index(op.f('ix_modifier_inventory_items_id'), 'modifier_inventory_items', ['id'], unique=False)
    op.create_index(op.f('ix_modifier_inventory_items_modifier_id'), 'modifier_inventory_items', ['modifier_id'], unique=False)
    op.create_index(op.f('ix_modifier_inventory_items_inventory_item_id'), 'modifier_inventory_items', ['inventory_item_id'], unique=False)

    # Create product_modifiers table
    op.create_table(
        'product_modifiers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('modifier_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modifier_id'], ['modifiers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', 'modifier_id', name='uq_product_modifier')
    )
    op.create_index(op.f('ix_product_modifiers_id'), 'product_modifiers', ['id'], unique=False)
    op.create_index(op.f('ix_product_modifiers_product_id'), 'product_modifiers', ['product_id'], unique=False)
    op.create_index(op.f('ix_product_modifiers_modifier_id'), 'product_modifiers', ['modifier_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_product_modifiers_modifier_id'), table_name='product_modifiers')
    op.drop_index(op.f('ix_product_modifiers_product_id'), table_name='product_modifiers')
    op.drop_index(op.f('ix_product_modifiers_id'), table_name='product_modifiers')
    op.drop_table('product_modifiers')

    op.drop_index(op.f('ix_modifier_inventory_items_inventory_item_id'), table_name='modifier_inventory_items')
    op.drop_index(op.f('ix_modifier_inventory_items_modifier_id'), table_name='modifier_inventory_items')
    op.drop_index(op.f('ix_modifier_inventory_items_id'), table_name='modifier_inventory_items')
    op.drop_table('modifier_inventory_items')

    op.drop_index(op.f('ix_modifiers_modifier_group_id'), table_name='modifiers')
    op.drop_index(op.f('ix_modifiers_id'), table_name='modifiers')
    op.drop_table('modifiers')

    op.drop_index(op.f('ix_modifier_groups_business_id'), table_name='modifier_groups')
    op.drop_index(op.f('ix_modifier_groups_id'), table_name='modifier_groups')
    op.drop_table('modifier_groups')
