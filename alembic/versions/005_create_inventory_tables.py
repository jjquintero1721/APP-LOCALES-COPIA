"""Create inventory tables (items and movements)

Revision ID: 005
Revises: 004
Create Date: 2025-12-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create inventory_items table
    op.create_table(
        'inventory_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('unit_of_measure', sa.String(50), nullable=False),
        sa.Column('sku', sa.String(100), nullable=True),
        sa.Column('quantity_in_stock', sa.Numeric(10, 3), nullable=False, server_default='0'),
        sa.Column('min_stock', sa.Numeric(10, 3), nullable=True),
        sa.Column('max_stock', sa.Numeric(10, 3), nullable=True),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('tax_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('include_tax', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['business_id'], ['business.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('quantity_in_stock >= 0', name='check_quantity_non_negative'),
        sa.CheckConstraint('unit_price >= 0', name='check_unit_price_non_negative')
    )
    op.create_index(op.f('ix_inventory_items_id'), 'inventory_items', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_items_business_id'), 'inventory_items', ['business_id'], unique=False)
    op.create_index(op.f('ix_inventory_items_supplier_id'), 'inventory_items', ['supplier_id'], unique=False)
    op.create_index(op.f('ix_inventory_items_sku'), 'inventory_items', ['sku'], unique=False)

    # Create inventory_movements table
    op.create_table(
        'inventory_movements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('inventory_item_id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('movement_type', sa.Enum('manual_in', 'manual_out', 'sale', 'transfer_in', 'transfer_out', 'recipe_consumption', 'revert', name='movementtype'), nullable=False),
        sa.Column('quantity', sa.Numeric(10, 3), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reverted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reverted_by_movement_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['inventory_item_id'], ['inventory_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['business_id'], ['business.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reverted_by_movement_id'], ['inventory_movements.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_movements_id'), 'inventory_movements', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_movements_inventory_item_id'), 'inventory_movements', ['inventory_item_id'], unique=False)
    op.create_index(op.f('ix_inventory_movements_business_id'), 'inventory_movements', ['business_id'], unique=False)
    op.create_index(op.f('ix_inventory_movements_created_by_user_id'), 'inventory_movements', ['created_by_user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_inventory_movements_created_by_user_id'), table_name='inventory_movements')
    op.drop_index(op.f('ix_inventory_movements_business_id'), table_name='inventory_movements')
    op.drop_index(op.f('ix_inventory_movements_inventory_item_id'), table_name='inventory_movements')
    op.drop_index(op.f('ix_inventory_movements_id'), table_name='inventory_movements')
    op.drop_table('inventory_movements')

    op.drop_index(op.f('ix_inventory_items_sku'), table_name='inventory_items')
    op.drop_index(op.f('ix_inventory_items_supplier_id'), table_name='inventory_items')
    op.drop_index(op.f('ix_inventory_items_business_id'), table_name='inventory_items')
    op.drop_index(op.f('ix_inventory_items_id'), table_name='inventory_items')
    op.drop_table('inventory_items')

    op.execute('DROP TYPE movementtype')
