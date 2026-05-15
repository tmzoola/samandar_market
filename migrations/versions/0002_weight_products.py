"""products: sold_by + unit_label; transaction_items.quantity → Numeric(12,3)

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-15

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Products: how the item is sold (per piece or by weight) and the
    # display label for fractional quantities (e.g. "kg").
    op.add_column(
        "products",
        sa.Column("sold_by", sa.String(length=16), nullable=False, server_default="unit"),
    )
    op.add_column(
        "products",
        sa.Column("unit_label", sa.String(length=8), nullable=True),
    )

    # Transaction items: allow fractional quantities so we can store
    # weights like 1.300 kg. Old integer rows (quantity=2) cast cleanly
    # to Numeric(12, 3) without loss.
    op.alter_column(
        "transaction_items",
        "quantity",
        existing_type=sa.Integer(),
        type_=sa.Numeric(12, 3),
        existing_nullable=False,
    )


def downgrade() -> None:
    # Truncate fractional quantities to integer on the way back.
    op.alter_column(
        "transaction_items",
        "quantity",
        existing_type=sa.Numeric(12, 3),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using="quantity::integer",
    )
    op.drop_column("products", "unit_label")
    op.drop_column("products", "sold_by")
