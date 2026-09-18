"""Add non-negative stock check constraint to product table

Revision ID: a1b2c3d4e5f6
Revises: 4fd0e73205a3
Create Date: 2026-09-18 19:49:00.000000

This migration adds a CHECK CONSTRAINT that enforces stock >= 0 at the
database level, serving as the last line of defence against stock going
negative due to application bugs or race conditions.

Safety note
-----------
If the database already contains rows with stock < 0 (data corruption),
this migration will fail.  Run the following query first to inspect and
repair bad data before applying this migration:

    -- Inspect
    SELECT id, name, stock FROM product WHERE stock < 0;

    -- Repair (set to 0)
    UPDATE product SET stock = 0 WHERE stock < 0;
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '4fd0e73205a3'
branch_labels = None
depends_on = None


def upgrade():
    # Use batch_alter_table for broad compatibility:
    #   - SQLite  : requires batch mode to recreate the table with the new constraint
    #   - PostgreSQL/MySQL : batch mode is transparent (just runs ALTER TABLE ADD CONSTRAINT)
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_product_stock_non_negative',
            'stock >= 0'
        )


def downgrade():
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.drop_constraint(
            'ck_product_stock_non_negative',
            type_='check'
        )
