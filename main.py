"""FastAPI entrypoint for the Samandar Market POS.

Serves the cashier dashboard and the admin panel, exposes the product
catalog + checkout API, and hosts the admin reporting endpoints
(daily / weekly / top-products / CSV export).
"""

from __future__ import annotations

import csv
import io
import logging
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

import crud
from auth import (
    clear_admin_cookie,
    create_admin_token,
    get_current_admin,
    set_admin_cookie,
    verify_password,
)
from database import get_session
from models import Admin, Product, Transaction
from schemas import (
    AdminLogin,
    AdminOut,
    CheckoutIn,
    DailyReport,
    DailySummary,
    HourlyBucket,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    TopProduct,
    TopProductsReport,
    TransactionItemOut,
    TransactionOut,
    WeeklyReport,
)
from seed import run_seed

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("pos")

PUBLIC_DIR = Path(__file__).parent / "public"


# ---------- Lifespan: seed ----------

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await run_seed()
    except Exception:
        log.exception("Seeding failed (will continue starting up)")
    yield


app = FastAPI(title="Samandar Market POS", lifespan=lifespan)


# ---------- Helpers ----------

def _serialize_product(p: Product) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "price": p.price,
        "category": p.category,
        "barcode": p.barcode,
        "emoji": p.emoji,
        "is_active": p.is_active,
        "sold_by": p.sold_by,
        "unit_label": p.unit_label,
    }


def _serialize_transaction(tx: Transaction) -> TransactionOut:
    from decimal import ROUND_HALF_UP, Decimal

    items_out = []
    for it in tx.items:
        qty = it.quantity if isinstance(it.quantity, Decimal) else Decimal(str(it.quantity))
        line_total = int(
            (Decimal(it.unit_price) * qty).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        items_out.append(TransactionItemOut(
            product_id=it.product_id,
            product_name=it.product.name if it.product else f"#{it.product_id}",
            quantity=float(qty),
            unit_price=it.unit_price,
            line_total=line_total,
            sold_by=it.product.sold_by if it.product else "unit",
            unit_label=it.product.unit_label if it.product else None,
        ))
    return TransactionOut(
        id=tx.id,
        total_amount=tx.total_amount,
        cash_received=tx.cash_received,
        change_amount=tx.change_amount,
        created_at=tx.created_at,
        items=items_out,
    )


# ---------- Health + static ----------

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


# ---------- Public catalog + checkout ----------

@app.get("/api/products")
async def get_products(db: AsyncSession = Depends(get_session)) -> dict:
    products = await crud.list_products(db, only_active=True)
    serialized = [_serialize_product(p) for p in products]
    categories: list[str] = []
    for item in serialized:
        if item["category"] not in categories:
            categories.append(item["category"])
    return {"products": serialized, "categories": categories}


@app.post("/api/checkout", response_model=TransactionOut)
async def checkout(
    payload: CheckoutIn,
    db: AsyncSession = Depends(get_session),
) -> TransactionOut:
    try:
        tx = await crud.create_transaction(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _serialize_transaction(tx)


@app.delete("/api/transactions/{tx_id}", status_code=204)
async def void_transaction(
    tx_id: int,
    db: AsyncSession = Depends(get_session),
) -> Response:
    """Void a just-completed sale. Used by the cashier's receipt modal.

    Hard-deletes the transaction + its items (FK is ON DELETE CASCADE).
    The dashboard only exposes this for the latest receipt, so the
    blast radius is naturally limited to the active customer.
    """
    tx = await db.get(Transaction, tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Tranzaksiya topilmadi")
    await db.delete(tx)
    await db.commit()
    return Response(status_code=204)


# ---------- Admin auth ----------

@app.post("/admin/login")
async def admin_login(
    payload: AdminLogin,
    response: Response,
    db: AsyncSession = Depends(get_session),
) -> dict:
    admin = await crud.get_admin_by_username(db, payload.username)
    if not admin or not verify_password(payload.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Login yoki parol noto'g'ri")
    token = create_admin_token(admin.id)
    set_admin_cookie(response, token)
    return {"status": "ok", "admin": AdminOut.model_validate(admin).model_dump(mode="json")}


@app.get("/admin/logout")
async def admin_logout(response: Response) -> dict:
    clear_admin_cookie(response)
    return {"status": "ok"}


@app.get("/admin/me", response_model=AdminOut)
async def admin_me(admin: Annotated[Admin, Depends(get_current_admin)]) -> Admin:
    return admin


# ---------- Admin: product CRUD ----------

@app.get("/admin/products", response_model=list[ProductOut])
async def admin_list_products(
    _admin: Annotated[Admin, Depends(get_current_admin)],
    db: AsyncSession = Depends(get_session),
) -> list[Product]:
    # Admins see all products, including soft-deleted ones.
    return await crud.list_products(db, only_active=False)


@app.post("/api/products", response_model=ProductOut, status_code=201)
async def create_product_endpoint(
    payload: ProductCreate,
    _admin: Annotated[Admin, Depends(get_current_admin)],
    db: AsyncSession = Depends(get_session),
) -> Product:
    return await crud.create_product(db, payload.model_dump())


@app.put("/api/products/{product_id}", response_model=ProductOut)
async def update_product_endpoint(
    product_id: int,
    payload: ProductUpdate,
    _admin: Annotated[Admin, Depends(get_current_admin)],
    db: AsyncSession = Depends(get_session),
) -> Product:
    product = await crud.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
    data = payload.model_dump(exclude_unset=True)
    return await crud.update_product(db, product, data)


@app.delete("/api/products/{product_id}")
async def delete_product_endpoint(
    product_id: int,
    _admin: Annotated[Admin, Depends(get_current_admin)],
    hard: bool = False,
    db: AsyncSession = Depends(get_session),
):
    """Delete a product.

    - Default (soft delete): flips `is_active=false`. Product disappears
      from the cashier dashboard but stays in the DB so past reports keep
      working.
    - `?hard=true` (hard delete): physically removes the row. Only allowed
      when the product has no sales history; otherwise returns 409.
    """
    product = await crud.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")

    if hard:
        try:
            await crud.hard_delete_product(db, product)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return Response(status_code=204)

    soft = await crud.soft_delete_product(db, product)
    return ProductOut.model_validate(soft)


# ---------- Reports ----------

def _parse_date(value: str | None, *, default: date) -> date:
    if not value:
        return default
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date: {value!r}, expected YYYY-MM-DD")


@app.get("/api/reports/daily", response_model=DailyReport)
async def daily_report(
    _admin: Annotated[Admin, Depends(get_current_admin)],
    date: str | None = None,
    db: AsyncSession = Depends(get_session),
) -> DailyReport:
    day = _parse_date(date, default=datetime.now().date())

    summary = await crud.daily_summary(db, day)
    hourly_rows = await crud.hourly_breakdown(db, day)
    top = await crud.top_products(db, start=day, end=day, limit=1)
    transactions = await crud.get_transactions_for_day(db, day)

    top_product = None
    if top:
        top_product = TopProduct(**top[0])

    avg = int(summary["revenue"] // summary["count"]) if summary["count"] else 0

    return DailyReport(
        date=day.isoformat(),
        total_revenue=summary["revenue"],
        transactions_count=summary["count"],
        average_transaction=avg,
        top_product=top_product,
        hourly=[HourlyBucket(**h) for h in hourly_rows],
        transactions=[_serialize_transaction(tx) for tx in transactions],
    )


@app.get("/api/reports/weekly", response_model=WeeklyReport)
async def weekly_report(
    _admin: Annotated[Admin, Depends(get_current_admin)],
    db: AsyncSession = Depends(get_session),
) -> WeeklyReport:
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    this_week_days = await crud.weekly_breakdown(db, end_day=today)
    last_week_days = await crud.weekly_breakdown(db, end_day=today - timedelta(days=7))

    def _agg(days_rows: list[dict]) -> dict:
        return {
            "revenue": sum(d["revenue"] for d in days_rows),
            "count": sum(d["count"] for d in days_rows),
        }

    today_summary = next((d for d in this_week_days if d["date"] == today.isoformat()), {
        "date": today.isoformat(), "revenue": 0, "count": 0,
    })
    yest_summary = next((d for d in this_week_days if d["date"] == yesterday.isoformat()),
                       await crud.daily_summary(db, yesterday))

    this_week = _agg(this_week_days)
    last_week = _agg(last_week_days)

    return WeeklyReport(
        today=DailySummary(**today_summary),
        yesterday=DailySummary(**yest_summary),
        this_week=DailySummary(
            date=today.isoformat(), revenue=this_week["revenue"], count=this_week["count"]
        ),
        last_week=DailySummary(
            date=(today - timedelta(days=7)).isoformat(),
            revenue=last_week["revenue"],
            count=last_week["count"],
        ),
        daily=[DailySummary(**d) for d in this_week_days],
    )


@app.get("/api/reports/top-products", response_model=TopProductsReport)
async def top_products_report(
    _admin: Annotated[Admin, Depends(get_current_admin)],
    period: str = "week",
    db: AsyncSession = Depends(get_session),
) -> TopProductsReport:
    today = datetime.now().date()
    if period == "day":
        start = today
    elif period == "week":
        start = today - timedelta(days=6)
    elif period == "month":
        start = today - timedelta(days=29)
    else:
        raise HTTPException(status_code=400, detail="period must be one of: day, week, month")

    rows = await crud.top_products(db, start=start, end=today, limit=5)
    return TopProductsReport(
        period=period,
        products=[TopProduct(**r) for r in rows],
    )


@app.get("/api/reports/export")
async def export_csv(
    _admin: Annotated[Admin, Depends(get_current_admin)],
    date: str | None = None,
    db: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    day = _parse_date(date, default=datetime.now().date())
    transactions = await crud.get_transactions_for_day(db, day)

    from decimal import ROUND_HALF_UP, Decimal as _D

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "transaction_id", "created_at", "product_id", "product_name",
        "sold_by", "unit_label", "quantity", "unit_price", "line_total",
        "transaction_total", "cash_received", "change_amount",
    ])
    for tx in transactions:
        for it in tx.items:
            qty = it.quantity if isinstance(it.quantity, _D) else _D(str(it.quantity))
            line = int((_D(it.unit_price) * qty).quantize(_D("1"), rounding=ROUND_HALF_UP))
            sold_by = it.product.sold_by if it.product else "unit"
            unit_label = (it.product.unit_label if it.product else None) or ""
            # For unit products write quantity as an integer; weight items keep 3 decimals.
            qty_out = str(int(qty)) if sold_by == "unit" else f"{qty:.3f}"
            writer.writerow([
                tx.id,
                tx.created_at.isoformat(),
                it.product_id,
                it.product.name if it.product else "",
                sold_by,
                unit_label,
                qty_out,
                it.unit_price,
                line,
                tx.total_amount,
                tx.cash_received,
                tx.change_amount,
            ])

    buf.seek(0)
    headers = {
        "Content-Disposition": f'attachment; filename="report_{day.isoformat()}.csv"',
    }
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv", headers=headers)


# ---------- Static files ----------

app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(PUBLIC_DIR / "index.html")


@app.get("/admin")
async def admin_page() -> FileResponse:
    # Admin SPA. Auth is enforced by the API calls it makes; the HTML
    # itself is safe to serve unauthenticated.
    return FileResponse(PUBLIC_DIR / "admin.html")
