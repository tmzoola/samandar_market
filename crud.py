"""Database access functions — CRUD + reporting aggregates.

Pricing math is done in integer UZS throughout to avoid float drift.
All datetimes are timezone-aware UTC; the cashier-facing dashboard
renders in the browser's local timezone, while admin reports bucket by
the Asia/Tashkent day boundary (UTC+5, no DST).
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable

from sqlalchemy import and_, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models import Admin, Product, Transaction, TransactionItem
from schemas import CheckoutIn

# All monetary math uses Decimal, then rounds half-up to whole UZS so the
# receipt total exactly equals the sum of displayed line totals.
_QTY_QUANT = Decimal("0.001")
_MONEY_ZERO = Decimal("1")


def _line_total(unit_price: int, quantity: Decimal) -> int:
    return int((Decimal(unit_price) * quantity).quantize(_MONEY_ZERO, rounding=ROUND_HALF_UP))

# Asia/Tashkent has no DST and is fixed at UTC+5. Bucketing by local-day
# is just "shift by 5h then take the date" — simple and reliable.
TASHKENT_OFFSET = timedelta(hours=5)


# ---------- Products ----------

async def list_products(db: AsyncSession, *, only_active: bool = True) -> list[Product]:
    stmt = select(Product)
    if only_active:
        stmt = stmt.where(Product.is_active.is_(True))
    stmt = stmt.order_by(Product.category, Product.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_product(db: AsyncSession, product_id: int) -> Product | None:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def create_product(db: AsyncSession, data: dict) -> Product:
    product = Product(**data)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def update_product(db: AsyncSession, product: Product, data: dict) -> Product:
    for key, value in data.items():
        if value is not None:
            setattr(product, key, value)
    await db.commit()
    await db.refresh(product)
    return product


async def soft_delete_product(db: AsyncSession, product: Product) -> Product:
    product.is_active = False
    await db.commit()
    await db.refresh(product)
    return product


async def hard_delete_product(db: AsyncSession, product: Product) -> None:
    """Physically remove a product. Refuses if it has any sales history.

    Letting a product go away while TransactionItems still reference it
    would either fail (FK is ON DELETE RESTRICT) or corrupt past reports.
    Caller must catch ValueError for the "has history" case.
    """
    refs_result = await db.execute(
        select(func.count())
        .select_from(TransactionItem)
        .where(TransactionItem.product_id == product.id)
    )
    refs = int(refs_result.scalar_one() or 0)
    if refs > 0:
        raise ValueError(
            f"Bu mahsulot {refs} ta tranzaksiyada ishlatilgan — butunlay "
            "o'chirib bo'lmaydi. Faqat nofaol qilish mumkin."
        )
    await db.delete(product)
    await db.commit()


# ---------- Checkout ----------

async def create_transaction(db: AsyncSession, payload: CheckoutIn) -> Transaction:
    # Load every product in one query and validate up front.
    ids = [item.product_id for item in payload.items]
    result = await db.execute(select(Product).where(Product.id.in_(ids)))
    products = {p.id: p for p in result.scalars().all()}

    missing = [i for i in ids if i not in products]
    if missing:
        raise ValueError(f"Unknown product ids: {missing}")
    inactive = [i for i in ids if not products[i].is_active]
    if inactive:
        raise ValueError(f"Product(s) not active: {inactive}")

    total = 0
    items: list[TransactionItem] = []
    for entry in payload.items:
        product = products[entry.product_id]
        unit_price = product.price
        qty = Decimal(str(entry.quantity)).quantize(_QTY_QUANT, rounding=ROUND_HALF_UP)
        if qty <= 0:
            raise ValueError(f"Quantity must be > 0 (product id={product.id})")
        # For unit products, refuse fractional quantities — you can't sell
        # 0.5 of a milk bottle. Weight products accept any positive Decimal.
        if product.sold_by == "unit" and qty != qty.to_integral_value():
            raise ValueError(
                f"«{product.name}» dona bilan sotiladi — quantity butun son bo'lishi kerak"
            )
        line = _line_total(unit_price, qty)
        total += line
        items.append(TransactionItem(
            product_id=product.id,
            quantity=qty,
            unit_price=unit_price,
        ))

    if payload.cash_received < total:
        raise ValueError(
            f"Insufficient cash: received {payload.cash_received}, required {total}"
        )

    transaction = Transaction(
        total_amount=total,
        cash_received=payload.cash_received,
        change_amount=payload.cash_received - total,
        items=items,
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return transaction


async def get_transactions_for_day(db: AsyncSession, day: date) -> list[Transaction]:
    start_local = datetime.combine(day, time.min)
    end_local = start_local + timedelta(days=1)
    start_utc = (start_local - TASHKENT_OFFSET).replace(tzinfo=timezone.utc)
    end_utc = (end_local - TASHKENT_OFFSET).replace(tzinfo=timezone.utc)

    stmt = (
        select(Transaction)
        .where(and_(Transaction.created_at >= start_utc, Transaction.created_at < end_utc))
        .order_by(Transaction.created_at)
    )
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())


# ---------- Reports ----------

async def daily_summary(db: AsyncSession, day: date) -> dict:
    """Aggregates for a single Tashkent-local day."""
    start_local = datetime.combine(day, time.min)
    end_local = start_local + timedelta(days=1)
    start_utc = (start_local - TASHKENT_OFFSET).replace(tzinfo=timezone.utc)
    end_utc = (end_local - TASHKENT_OFFSET).replace(tzinfo=timezone.utc)

    totals = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.total_amount), 0),
            func.count(Transaction.id),
        ).where(and_(Transaction.created_at >= start_utc, Transaction.created_at < end_utc))
    )
    total_revenue, count = totals.one()
    return {
        "date": day.isoformat(),
        "revenue": int(total_revenue or 0),
        "count": int(count or 0),
    }


async def hourly_breakdown(db: AsyncSession, day: date) -> list[dict]:
    """24 hourly buckets in Tashkent local time."""
    start_local = datetime.combine(day, time.min)
    end_local = start_local + timedelta(days=1)
    start_utc = (start_local - TASHKENT_OFFSET).replace(tzinfo=timezone.utc)
    end_utc = (end_local - TASHKENT_OFFSET).replace(tzinfo=timezone.utc)

    # Shift to Tashkent local then bucket by hour.
    hour_expr = func.extract(
        "hour",
        Transaction.created_at + TASHKENT_OFFSET,
    )

    stmt = (
        select(
            hour_expr.label("hour"),
            func.coalesce(func.sum(Transaction.total_amount), 0).label("revenue"),
            func.count(Transaction.id).label("count"),
        )
        .where(and_(Transaction.created_at >= start_utc, Transaction.created_at < end_utc))
        .group_by("hour")
    )
    result = await db.execute(stmt)
    by_hour = {int(row.hour): row for row in result.all()}

    buckets = []
    for h in range(24):
        row = by_hour.get(h)
        buckets.append({
            "hour": h,
            "revenue": int(row.revenue) if row else 0,
            "count": int(row.count) if row else 0,
        })
    return buckets


async def top_products(
    db: AsyncSession,
    *,
    start: date,
    end: date,
    limit: int = 5,
) -> list[dict]:
    """Top N products by quantity sold over the [start, end] Tashkent date range."""
    start_local = datetime.combine(start, time.min)
    end_local = datetime.combine(end, time.min) + timedelta(days=1)
    start_utc = (start_local - TASHKENT_OFFSET).replace(tzinfo=timezone.utc)
    end_utc = (end_local - TASHKENT_OFFSET).replace(tzinfo=timezone.utc)

    stmt = (
        select(
            Product.id,
            Product.name,
            Product.sold_by,
            Product.unit_label,
            func.sum(TransactionItem.quantity).label("qty"),
            func.sum(TransactionItem.quantity * TransactionItem.unit_price).label("revenue"),
        )
        .join(TransactionItem, TransactionItem.product_id == Product.id)
        .join(Transaction, Transaction.id == TransactionItem.transaction_id)
        .where(and_(Transaction.created_at >= start_utc, Transaction.created_at < end_utc))
        .group_by(Product.id, Product.name, Product.sold_by, Product.unit_label)
        # Ordering by revenue is the only fair comparison once you mix unit
        # and weight products in one list — `sum(quantity)` would compare
        # "kg of rice" to "bottles of milk".
        .order_by(desc("revenue"))
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [
        {
            "product_id": pid,
            "name": name,
            "sold_by": sold_by,
            "unit_label": unit_label,
            "quantity": float(qty or 0),
            "revenue": int(revenue or 0),
        }
        for pid, name, sold_by, unit_label, qty, revenue in result.all()
    ]


async def weekly_breakdown(db: AsyncSession, *, end_day: date) -> list[dict]:
    """Returns 7 daily summaries ending on `end_day` (inclusive)."""
    days = [end_day - timedelta(days=6 - i) for i in range(7)]
    return [await daily_summary(db, d) for d in days]


# ---------- Admins ----------

async def get_admin_by_username(db: AsyncSession, username: str) -> Admin | None:
    result = await db.execute(select(Admin).where(Admin.username == username))
    return result.scalar_one_or_none()


async def count_admins(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(Admin))
    return int(result.scalar_one() or 0)


async def count_products(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(Product))
    return int(result.scalar_one() or 0)


async def bulk_create_products(db: AsyncSession, items: Iterable[dict]) -> int:
    n = 0
    for item in items:
        db.add(Product(**item))
        n += 1
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise
    return n


async def create_admin(db: AsyncSession, username: str, hashed_password: str) -> Admin:
    admin = Admin(username=username, hashed_password=hashed_password)
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin
