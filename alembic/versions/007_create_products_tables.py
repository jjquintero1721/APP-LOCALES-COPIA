"""Create products and product_ingredients tables

Revision ID: 007
Revises: 006
Create Date: 2025-12-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('sale_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_cost', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('profit_margin_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('profit_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['business_id'], ['business.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('sale_price >= 0', name='check_sale_price_non_negative'),
        sa.CheckConstraint('total_cost >= 0', name='check_total_cost_non_negative'),
        sa.CheckConstraint('sale_price >= total_cost', name='check_sale_price_gte_total_cost')
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_business_id'), 'products', ['business_id'], unique=False)

    # Create product_ingredients table
    op.create_table(
        'product_ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('inventory_item_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(10, 3), nullable=False),
        sa.Column('unit_cost', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_cost', sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inventory_item_id'], ['inventory_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', 'inventory_item_id', name='uq_product_ingredient'),
        sa.CheckConstraint('quantity > 0', name='check_ingredient_quantity_positive'),
        sa.CheckConstraint('unit_cost >= 0', name='check_ingredient_unit_cost_non_negative'),
        sa.CheckConstraint('total_cost >= 0', name='check_ingredient_total_cost_non_negative')
    )
    op.create_index(op.f('ix_product_ingredients_id'), 'product_ingredients', ['id'], unique=False)
    op.create_index(op.f('ix_product_ingredients_product_id'), 'product_ingredients', ['product_id'], unique=False)
    op.create_index(op.f('ix_product_ingredients_inventory_item_id'), 'product_ingredients', ['inventory_item_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_product_ingredients_inventory_item_id'), table_name='product_ingredients')
    op.drop_index(op.f('ix_product_ingredients_product_id'), table_name='product_ingredients')
    op.drop_index(op.f('ix_product_ingredients_id'), table_name='product_ingredients')
    op.drop_table('product_ingredients')

    op.drop_index(op.f('ix_products_business_id'), table_name='products')
    op.drop_index(op.f('ix_products_id'), table_name='products')
    op.drop_table('products')
