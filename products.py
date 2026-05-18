"""Static product catalog for the POS.

Prices are in UZS (Uzbek Som). Keep entries simple — id, name, price,
category, emoji — so the frontend can render cards directly and the
Telegram bot can fuzzy-match spoken names against ``name``.

`sold_by` is "unit" for piece-priced items and "weight" for bulk items
where the price is per `unit_label` (typically per kg).

`stock` and `low_stock_threshold` are *initial* values used only on a
fresh install seed. After the first run, the database is the source of
truth — edit products via the admin panel.
"""

PRODUCTS = [
    # Sut mahsulotlari (Dairy)
    {"id": 1, "name": "Sut 1L", "price": 12000, "category": "Sut mahsulotlari", "emoji": "🥛", "stock": 40, "low_stock_threshold": 8},
    {"id": 2, "name": "Qatiq 500g", "price": 8000, "category": "Sut mahsulotlari", "emoji": "🥣", "stock": 30, "low_stock_threshold": 6},
    {"id": 3, "name": "Smetana 200g", "price": 15000, "category": "Sut mahsulotlari", "emoji": "🥄", "stock": 20, "low_stock_threshold": 5},
    {"id": 4, "name": "Pishloq 200g", "price": 35000, "category": "Sut mahsulotlari", "emoji": "🧀", "stock": 15, "low_stock_threshold": 4},
    {"id": 5, "name": "Sariyog' 200g", "price": 25000, "category": "Sut mahsulotlari", "emoji": "🧈", "stock": 20, "low_stock_threshold": 5},

    # Non mahsulotlari (Bread)
    {"id": 6, "name": "Non (oddiy)", "price": 4000, "category": "Non mahsulotlari", "emoji": "🥖", "stock": 60, "low_stock_threshold": 15},
    {"id": 7, "name": "Lavash", "price": 5000, "category": "Non mahsulotlari", "emoji": "🫓", "stock": 40, "low_stock_threshold": 10},
    {"id": 8, "name": "Patir non", "price": 6000, "category": "Non mahsulotlari", "emoji": "🍞", "stock": 30, "low_stock_threshold": 8},
    {"id": 9, "name": "Bulochka", "price": 3000, "category": "Non mahsulotlari", "emoji": "🥯", "stock": 50, "low_stock_threshold": 12},

    # Ichimliklar (Drinks)
    {"id": 10, "name": "Choy Lipton 100g", "price": 18000, "category": "Ichimliklar", "emoji": "🍵", "stock": 25, "low_stock_threshold": 5},
    {"id": 11, "name": "Coca-Cola 1.5L", "price": 15000, "category": "Ichimliklar", "emoji": "🥤", "stock": 40, "low_stock_threshold": 10},
    {"id": 12, "name": "Mineral suv 1L", "price": 4000, "category": "Ichimliklar", "emoji": "💧", "stock": 80, "low_stock_threshold": 20},
    {"id": 13, "name": "Olma sharbati 1L", "price": 12000, "category": "Ichimliklar", "emoji": "🧃", "stock": 25, "low_stock_threshold": 6},
    {"id": 14, "name": "Pepsi 0.5L", "price": 8000, "category": "Ichimliklar", "emoji": "🥤", "stock": 50, "low_stock_threshold": 12},

    # Shirinliklar (Snacks)
    {"id": 15, "name": "Chips Lay's", "price": 9000, "category": "Shirinliklar", "emoji": "🍟", "stock": 40, "low_stock_threshold": 10},
    {"id": 16, "name": "Pista 200g", "price": 45000, "category": "Shirinliklar", "emoji": "🥜", "stock": 15, "low_stock_threshold": 4},
    {"id": 17, "name": "Shokolad Snickers", "price": 14000, "category": "Shirinliklar", "emoji": "🍫", "stock": 40, "low_stock_threshold": 10},
    {"id": 18, "name": "Pechene 300g", "price": 7000, "category": "Shirinliklar", "emoji": "🍪", "stock": 30, "low_stock_threshold": 8},
    {"id": 19, "name": "Konfet 200g", "price": 6000, "category": "Shirinliklar", "emoji": "🍬", "stock": 25, "low_stock_threshold": 6},

    # Meva-sabzavot (Fruits & Vegetables) — sold by weight (price per kg)
    {"id": 20, "name": "Olma", "price": 12000, "category": "Meva-sabzavot", "emoji": "🍎", "sold_by": "weight", "unit_label": "kg", "stock": 30.0, "low_stock_threshold": 5.0},
    {"id": 21, "name": "Banan", "price": 18000, "category": "Meva-sabzavot", "emoji": "🍌", "sold_by": "weight", "unit_label": "kg", "stock": 20.0, "low_stock_threshold": 4.0},
    {"id": 22, "name": "Pomidor", "price": 10000, "category": "Meva-sabzavot", "emoji": "🍅", "sold_by": "weight", "unit_label": "kg", "stock": 25.0, "low_stock_threshold": 5.0},
    {"id": 23, "name": "Kartoshka", "price": 5000, "category": "Meva-sabzavot", "emoji": "🥔", "sold_by": "weight", "unit_label": "kg", "stock": 80.0, "low_stock_threshold": 15.0},
    {"id": 24, "name": "Piyoz", "price": 4000, "category": "Meva-sabzavot", "emoji": "🧅", "sold_by": "weight", "unit_label": "kg", "stock": 50.0, "low_stock_threshold": 10.0},

    # Yormalar (Grains, sold by weight)
    {"id": 25, "name": "Guruch (oddiy)", "price": 14000, "category": "Yormalar", "emoji": "🍚", "sold_by": "weight", "unit_label": "kg", "stock": 100.0, "low_stock_threshold": 20.0},
    {"id": 26, "name": "Shakar", "price": 11000, "category": "Yormalar", "emoji": "🍬", "sold_by": "weight", "unit_label": "kg", "stock": 60.0, "low_stock_threshold": 15.0},
    {"id": 27, "name": "Un", "price": 7000, "category": "Yormalar", "emoji": "🌾", "sold_by": "weight", "unit_label": "kg", "stock": 80.0, "low_stock_threshold": 20.0},
]


CATEGORIES: list[str] = []
for _p in PRODUCTS:
    if _p["category"] not in CATEGORIES:
        CATEGORIES.append(_p["category"])


def get_product(product_id: int) -> dict | None:
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    return None
