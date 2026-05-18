"""One-time seed data — runs on startup if the relevant tables are empty.

- Seeds 24 sample products from products.py
- Creates a default admin (username/password from env or admin/admin123)
"""

from __future__ import annotations

import logging
import os

from auth import hash_password
from crud import (
    bulk_create_products,
    count_admins,
    count_products,
    create_admin,
    get_admin_by_username,
)
from database import SessionLocal
from products import PRODUCTS

log = logging.getLogger("seed")

DEFAULT_ADMIN_USERNAME = os.getenv("ADMIN_DEFAULT_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_DEFAULT_PASSWORD", "admin123")


async def seed_products() -> int:
    async with SessionLocal() as db:
        existing = await count_products(db)
        if existing > 0:
            log.info("Skipping product seed (table has %d rows)", existing)
            return 0
        rows = [
            {
                "name": p["name"],
                "price": p["price"],
                "category": p["category"],
                "emoji": p.get("emoji"),
                "barcode": None,
                "is_active": True,
                "sold_by": p.get("sold_by", "unit"),
                "unit_label": p.get("unit_label"),
                "stock": p.get("stock", 0),
                "low_stock_threshold": p.get("low_stock_threshold"),
            }
            for p in PRODUCTS
        ]
        n = await bulk_create_products(db, rows)
        log.info("Seeded %d products", n)
        return n


async def seed_admin() -> bool:
    async with SessionLocal() as db:
        if await count_admins(db) > 0:
            log.info("Skipping admin seed (at least one admin exists)")
            return False
        # Defensive: a previous attempt may have left a partial state.
        existing = await get_admin_by_username(db, DEFAULT_ADMIN_USERNAME)
        if existing:
            return False
        await create_admin(
            db,
            username=DEFAULT_ADMIN_USERNAME,
            hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
        )
        log.warning(
            "Created default admin: username=%s password=%s — CHANGE THIS",
            DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD,
        )
        return True


async def run_seed() -> None:
    await seed_products()
    await seed_admin()
