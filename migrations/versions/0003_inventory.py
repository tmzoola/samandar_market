"""products.stock + low_stock_threshold; stock_movements ledger

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-18

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "stock",
            sa.Numeric(14, 3),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "low_stock_threshold",
            sa.Numeric(12, 3),
            nullable=True,
        ),
    )

    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Positive delta = stock added, negative = stock removed.
        sa.Column("delta", sa.Numeric(14, 3), nullable=False),
        # Balance after applying the delta — denormalised for cheap reads
        # and to make manual reconciliation possible.
        sa.Column("balance_after", sa.Numeric(14, 3), nullable=False),
        # One of: "sale", "refill", "adjustment", "void".
        sa.Column("reason", sa.String(length=32), nullable=False),
        # Optional link to the sale that caused this movement. SET NULL on
        # transaction delete (void) so the audit row survives.
        sa.Column(
            "transaction_id",
            sa.Integer(),
            sa.ForeignKey("transactions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_stock_movements_product_created",
        "stock_movements",
        ["product_id", "created_at"],
    )
    op.create_index(
        "ix_stock_movements_reason",
        "stock_movements",
        ["reason"],
    )


def downgrade() -> None:
    op.drop_index("ix_stock_movements_reason", table_name="stock_movements")
    op.drop_index("ix_stock_movements_product_created", table_name="stock_movements")
    op.drop_table("stock_movements")
    op.drop_column("products", "low_stock_threshold")
    op.drop_column("products", "stock")
