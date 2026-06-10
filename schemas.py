"""Pydantic request/response models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SoldBy = Literal["unit", "weight"]


# ---------- Products ----------

class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    price: int = Field(ge=0)
    category: str = Field(min_length=1, max_length=100)
    barcode: str | None = Field(default=None, max_length=64)
    emoji: str | None = Field(default=None, max_length=8)
    is_active: bool = True
    sold_by: SoldBy = "unit"
    unit_label: str | None = Field(default=None, max_length=8)
    # Initial stock when creating; current stock when updating.
    stock: float = 0
    low_stock_threshold: float | None = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    price: int | None = Field(default=None, ge=0)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    barcode: str | None = Field(default=None, max_length=64)
    emoji: str | None = Field(default=None, max_length=8)
    is_active: bool | None = None
    sold_by: SoldBy | None = None
    unit_label: str | None = Field(default=None, max_length=8)
    # Note: editing `stock` directly here writes the raw value WITHOUT a
    # movement row — use /api/inventory/{id}/adjust for tracked changes.
    stock: float | None = None
    low_stock_threshold: float | None = None


class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------- Inventory ----------

class StockMovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    delta: float
    balance_after: float
    reason: str
    transaction_id: int | None
    note: str | None
    created_at: datetime


class RefillIn(BaseModel):
    """Add to current stock — typical "supplier delivered N kg/units"."""
    quantity: float = Field(gt=0)
    note: str | None = Field(default=None, max_length=255)


class AdjustIn(BaseModel):
    """Set stock to an exact value — typical "physical recount said N"."""
    new_stock: float = Field(ge=0)
    note: str = Field(min_length=1, max_length=255)


class InventoryItem(BaseModel):
    """Row in the admin inventory view."""
    product_id: int
    name: str
    emoji: str | None
    category: str
    sold_by: SoldBy
    unit_label: str | None
    stock: float
    low_stock_threshold: float | None
    is_active: bool
    # "ok" | "low" | "out"
    status: str


class InventoryReport(BaseModel):
    total_products: int
    out_of_stock: int
    low_stock: int
    items: list[InventoryItem]


# ---------- Checkout / Transactions ----------

class CheckoutItem(BaseModel):
    product_id: int
    # Float so weight items (1.3 kg) come over the wire cleanly. The server
    # casts to Decimal with 3-place quantization before computing money.
    quantity: float = Field(gt=0)


class CheckoutIn(BaseModel):
    items: list[CheckoutItem] = Field(min_length=1)
    cash_received: int = Field(ge=0)


class TransactionItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: int
    product_name: str
    quantity: float
    unit_price: int
    line_total: int
    sold_by: SoldBy = "unit"
    unit_label: str | None = None


class TransactionOut(BaseModel):
    id: int
    total_amount: int
    cash_received: int
    change_amount: int
    created_at: datetime
    items: list[TransactionItemOut]


# ---------- Admin auth ----------

class AdminLogin(BaseModel):
    username: str
    password: str


class AdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    created_at: datetime


# ---------- Reports ----------

class TopProduct(BaseModel):
    product_id: int
    name: str
    quantity: float
    revenue: int
    sold_by: SoldBy = "unit"
    unit_label: str | None = None


class HourlyBucket(BaseModel):
    hour: int
    revenue: int
    count: int


class DailyReport(BaseModel):
    date: str
    total_revenue: int
    transactions_count: int
    average_transaction: int
    top_product: TopProduct | None
    hourly: list[HourlyBucket]
    transactions: list[TransactionOut]


class DailySummary(BaseModel):
    date: str
    revenue: int
    count: int


class WeeklyReport(BaseModel):
    today: DailySummary
    yesterday: DailySummary
    this_week: DailySummary
    last_week: DailySummary
    daily: list[DailySummary]


class TopProductsReport(BaseModel):
    period: str
    products: list[TopProduct]
