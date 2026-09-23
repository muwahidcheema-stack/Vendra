"""A few Changes in All Models

Revision ID: 987619b7196f
Revises: d9a7b4964ad3
Create Date: 2026-09-23 23:41:23.120549

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '987619b7196f'
down_revision: Union[str, Sequence[str], None] = 'd9a7b4964ad3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Declare enum representations explicitly
ORDER_STATUS_VALUES = ('PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'CANCELLED', 'DELIVERED')
orderstatus_enum = postgresql.ENUM(*ORDER_STATUS_VALUES, name='orderstatus')
old_orderstatus_enum = postgresql.ENUM(*ORDER_STATUS_VALUES, name='orderstaus')


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Explicitly create the corrected Postgres enum type first
    orderstatus_enum.create(op.get_bind(), checkfirst=True)

    op.create_table('wishlists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'product_id', name='uq_wishlist_user_product')
    )
    op.create_index(op.f('ix_wishlists_id'), 'wishlists', ['id'], unique=False)
    op.create_index(op.f('ix_wishlists_user_id'), 'wishlists', ['user_id'], unique=False)
    op.drop_index(op.f('ix_wishlist_id'), table_name='wishlist')
    op.drop_index(op.f('ix_wishlist_user_id'), table_name='wishlist')
    op.drop_table('wishlist')

    op.alter_column('cart_items', 'created_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False
    )
    op.create_unique_constraint('uq_cart_user_product', 'cart_items', ['user_id', 'product_id'])

    op.alter_column('order_items', 'product_id',
        existing_type=sa.INTEGER(),
        nullable=True
    )
    op.alter_column('order_items', 'created_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False
    )
    op.drop_constraint(op.f('order_items_product_id_fkey'), 'order_items', type_='foreignkey')
    op.create_foreign_key(None, 'order_items', 'products', ['product_id'], ['id'], ondelete='SET NULL')

    # 2. Alter orders.status column using the created enum and text casting
    op.alter_column('orders', 'status',
        existing_type=old_orderstatus_enum,
        type_=orderstatus_enum,
        existing_nullable=False,
        postgresql_using="status::text::orderstatus"
    )

    op.alter_column('orders', 'created_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False
    )
    op.alter_column('products', 'created_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False
    )
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)

    op.alter_column('reviews', 'created_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False
    )
    op.create_unique_constraint('uq_review_user_product_order', 'reviews', ['user_id', 'product_id', 'order_id'])

    op.alter_column('users', 'created_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Ensure the old typo enum exists if rolling back
    old_orderstatus_enum.create(op.get_bind(), checkfirst=True)

    op.alter_column('users', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False
    )
    op.drop_constraint('uq_review_user_product_order', 'reviews', type_='unique')
    op.alter_column('reviews', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False
    )
    op.drop_index(op.f('ix_products_category_id'), table_name='products')
    op.alter_column('products', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False
    )
    op.alter_column('orders', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False
    )

    op.alter_column('orders', 'status',
        existing_type=orderstatus_enum,
        type_=old_orderstatus_enum,
        existing_nullable=False,
        postgresql_using="status::text::orderstaus"
    )

    op.drop_constraint(None, 'order_items', type_='foreignkey')
    op.create_foreign_key(op.f('order_items_product_id_fkey'), 'order_items', 'products', ['product_id'], ['id'], ondelete='CASCADE')
    op.alter_column('order_items', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False
    )
    op.alter_column('order_items', 'product_id',
        existing_type=sa.INTEGER(),
        nullable=False
    )
    op.drop_constraint('uq_cart_user_product', 'cart_items', type_='unique')
    op.alter_column('cart_items', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False
    )
    op.create_table('wishlist',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('product_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name=op.f('wishlist_product_id_fkey'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('wishlist_user_id_fkey'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('wishlist_pkey'))
    )
    op.create_index(op.f('ix_wishlist_user_id'), 'wishlist', ['user_id'], unique=False)
    op.create_index(op.f('ix_wishlist_id'), 'wishlist', ['id'], unique=False)
    op.drop_index(op.f('ix_wishlists_user_id'), table_name='wishlists')
    op.drop_index(op.f('ix_wishlists_id'), table_name='wishlists')
    op.drop_table('wishlists')

    # Drop the new enum upon full downgrade
    orderstatus_enum.drop(op.get_bind(), checkfirst=True)