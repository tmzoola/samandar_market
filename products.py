"""Static product catalog for the POS.

Prices are in UZS (Uzbek Som). Keep entries simple — id, name, price,
category, emoji — so the frontend can render cards directly and the
Telegram bot can fuzzy-match spoken names against ``name``.
"""

PRODUCTS = [
    # Sut mahsulotlari (Dairy)
    {"id": 1, "name": "Sut 1L", "price": 12000, "category": "Sut mahsulotlari", "emoji": "🥛"},
    {"id": 2, "name": "Qatiq 500g", "price": 8000, "category": "Sut mahsulotlari", "emoji": "🥣"},
    {"id": 3, "name": "Smetana 200g", "price": 15000, "category": "Sut mahsulotlari", "emoji": "🥄"},
    {"id": 4, "name": "Pishloq 200g", "price": 35000, "category": "Sut mahsulotlari", "emoji": "🧀"},
    {"id": 5, "name": "Sariyog' 200g", "price": 25000, "category": "Sut mahsulotlari", "emoji": "🧈"},

    # Non mahsulotlari (Bread)
    {"id": 6, "name": "Non (oddiy)", "price": 4000, "category": "Non mahsulotlari", "emoji": "🥖"},
    {"id": 7, "name": "Lavash", "price": 5000, "category": "Non mahsulotlari", "emoji": "🫓"},
    {"id": 8, "name": "Patir non", "price": 6000, "category": "Non mahsulotlari", "emoji": "🍞"},
    {"id": 9, "name": "Bulochka", "price": 3000, "category": "Non mahsulotlari", "emoji": "🥯"},

    # Ichimliklar (Drinks)
    {"id": 10, "name": "Choy Lipton 100g", "price": 18000, "category": "Ichimliklar", "emoji": "🍵"},
    {"id": 11, "name": "Coca-Cola 1.5L", "price": 15000, "category": "Ichimliklar", "emoji": "🥤"},
    {"id": 12, "name": "Mineral suv 1L", "price": 4000, "category": "Ichimliklar", "emoji": "💧"},
    {"id": 13, "name": "Olma sharbati 1L", "price": 12000, "category": "Ichimliklar", "emoji": "🧃"},
    {"id": 14, "name": "Pepsi 0.5L", "price": 8000, "category": "Ichimliklar", "emoji": "🥤"},

    # Shirinliklar (Snacks)
    {"id": 15, "name": "Chips Lay's", "price": 9000, "category": "Shirinliklar", "emoji": "🍟"},
    {"id": 16, "name": "Pista 200g", "price": 45000, "category": "Shirinliklar", "emoji": "🥜"},
    {"id": 17, "name": "Shokolad Snickers", "price": 14000, "category": "Shirinliklar", "emoji": "🍫"},
    {"id": 18, "name": "Pechene 300g", "price": 7000, "category": "Shirinliklar", "emoji": "🍪"},
    {"id": 19, "name": "Konfet 200g", "price": 6000, "category": "Shirinliklar", "emoji": "🍬"},

    # Meva-sabzavot (Fruits & Vegetables) — sold by weight (price per kg)
    {"id": 20, "name": "Olma", "price": 12000, "category": "Meva-sabzavot", "emoji": "🍎", "sold_by": "weight", "unit_label": "kg"},
    {"id": 21, "name": "Banan", "price": 18000, "category": "Meva-sabzavot", "emoji": "🍌", "sold_by": "weight", "unit_label": "kg"},
    {"id": 22, "name": "Pomidor", "price": 10000, "category": "Meva-sabzavot", "emoji": "🍅", "sold_by": "weight", "unit_label": "kg"},
    {"id": 23, "name": "Kartoshka", "price": 5000, "category": "Meva-sabzavot", "emoji": "🥔", "sold_by": "weight", "unit_label": "kg"},
    {"id": 24, "name": "Piyoz", "price": 4000, "category": "Meva-sabzavot", "emoji": "🧅", "sold_by": "weight", "unit_label": "kg"},

    # Yormalar (Grains, sold by weight)
    {"id": 25, "name": "Guruch (oddiy)", "price": 14000, "category": "Yormalar", "emoji": "🍚", "sold_by": "weight", "unit_label": "kg"},
    {"id": 26, "name": "Shakar", "price": 11000, "category": "Yormalar", "emoji": "🍬", "sold_by": "weight", "unit_label": "kg"},
    {"id": 27, "name": "Un", "price": 7000, "category": "Yormalar", "emoji": "🌾", "sold_by": "weight", "unit_label": "kg"},
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
