"""
generate_data.py

Quick script I wrote to spin up a fake but realistic e-commerce dataset.
Uses Faker + numpy to get varied names, emails, dates etc.
Outputs 4 CSVs into /data — run this first before load_db.py
"""

import os
import random
import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# tweak these if you want more/less data
N_CUSTOMERS = 1_000
N_PRODUCTS  = 120
N_ORDERS    = 5_000
START_DATE  = datetime(2024, 1, 1)
END_DATE    = datetime(2025, 12, 31)

REGIONS         = ["West", "East", "South", "Midwest"]
REGION_WEIGHTS  = [0.35, 0.30, 0.20, 0.15]

SEGMENTS        = ["Premium", "Regular", "Budget"]
SEGMENT_WEIGHTS = [0.20, 0.55, 0.25]

CATEGORIES = {
    "Electronics":   ["Smartphones", "Laptops", "Accessories", "Wearables"],
    "Apparel":       ["Shirts", "Pants", "Footwear", "Outerwear"],
    "Home & Garden": ["Furniture", "Decor", "Kitchen", "Tools"],
    "Sports":        ["Equipment", "Clothing", "Footwear", "Nutrition"],
    "Beauty":        ["Skincare", "Haircare", "Makeup", "Fragrance"],
}

ORDER_STATUSES = ["Delivered", "Shipped", "Cancelled", "Returned", "Processing"]
STATUS_WEIGHTS = [0.72, 0.12, 0.08, 0.05, 0.03]


def sample_order_dates(n, start, end):
    """
    Sample n dates weighted by month — Nov/Dec get ~3x weight to simulate
    the holiday spike. Jan gets a small bump (post-holiday), summer too.
    """
    days = (end - start).days
    all_dates = [start + timedelta(days=i) for i in range(days + 1)]

    weights = []
    for d in all_dates:
        m = d.month
        if m in (11, 12):
            w = 3.0
        elif m == 1:
            w = 1.3
        elif m in (6, 7, 8):
            w = 1.4
        else:
            w = 1.0
        weights.append(w)

    total = sum(weights)
    probs = [w / total for w in weights]
    idx = np.random.choice(len(all_dates), size=n, replace=True, p=probs)
    return [all_dates[i] for i in idx]


# Customers
print("Generating customers...")

churn_cutoff = START_DATE + timedelta(days=180)

customer_ids = [f"C{str(i).zfill(5)}" for i in range(1, N_CUSTOMERS + 1)]
signup_dates = [START_DATE + timedelta(days=int(d))
                for d in np.random.exponential(scale=300, size=N_CUSTOMERS)]
signup_dates = [min(d, END_DATE - timedelta(days=1)) for d in signup_dates]

# ~30% of early signups churn (stop ordering) — simulates realistic churn behaviour
is_churned = [
    (sd < churn_cutoff) and (random.random() < 0.30)
    for sd in signup_dates
]

customers_df = pd.DataFrame({
    "customer_id": customer_ids,
    "name":        [fake.name() for _ in range(N_CUSTOMERS)],
    "email":       [fake.email() for _ in range(N_CUSTOMERS)],
    "signup_date": [d.strftime("%Y-%m-%d") for d in signup_dates],
    "region":      np.random.choice(REGIONS, size=N_CUSTOMERS, p=REGION_WEIGHTS),
    "segment":     np.random.choice(SEGMENTS, size=N_CUSTOMERS, p=SEGMENT_WEIGHTS),
    "_churned":    is_churned,
})

churn_ids  = set(customers_df.loc[customers_df["_churned"], "customer_id"])
active_ids = set(customers_df.loc[~customers_df["_churned"], "customer_id"])

customers_out = customers_df.drop(columns=["_churned"])
customers_out.to_csv(os.path.join(OUTPUT_DIR, "customers.csv"), index=False)
print(f"  -> {len(customers_out):,} customers")


# Products
print("Generating products...")

product_rows = []
pid = 1
for category, sub_cats in CATEGORIES.items():
    n_per_sub = N_PRODUCTS // (len(CATEGORIES) * len(sub_cats))
    for sub in sub_cats:
        count = n_per_sub + (1 if sub == sub_cats[-1] else 0)
        for _ in range(count):
            cost  = round(random.uniform(5, 400), 2)
            margin = random.uniform(0.15, 0.65)
            price = round(cost * (1 + margin), 2)
            product_rows.append({
                "product_id":   f"P{str(pid).zfill(5)}",
                "name":         f"{fake.word().capitalize()} {sub[:-1] if sub.endswith('s') else sub}",
                "category":     category,
                "sub_category": sub,
                "price":        price,
                "cost":         cost,
            })
            pid += 1

# top up to exactly N_PRODUCTS
while len(product_rows) < N_PRODUCTS:
    cat  = random.choice(list(CATEGORIES.keys()))
    sub  = random.choice(CATEGORIES[cat])
    cost = round(random.uniform(5, 400), 2)
    price = round(cost * random.uniform(1.15, 1.65), 2)
    product_rows.append({
        "product_id":   f"P{str(pid).zfill(5)}",
        "name":         f"{fake.word().capitalize()} {sub}",
        "category":     cat,
        "sub_category": sub,
        "price":        price,
        "cost":         cost,
    })
    pid += 1

products_df = pd.DataFrame(product_rows[:N_PRODUCTS])
products_df.to_csv(os.path.join(OUTPUT_DIR, "products.csv"), index=False)
print(f"  -> {len(products_df):,} products")


# Orders
print("Generating orders...")

order_dates  = sample_order_dates(N_ORDERS, START_DATE, END_DATE)
active_list  = list(active_ids)
churned_list = list(churn_ids)

assigned_customers = []
for d in order_dates:
    # churned customers only appear in early orders
    if d < churn_cutoff and churned_list and random.random() < 0.25:
        assigned_customers.append(random.choice(churned_list))
    else:
        assigned_customers.append(random.choice(active_list))

orders_df = pd.DataFrame({
    "order_id":      [f"O{str(i).zfill(6)}" for i in range(1, N_ORDERS + 1)],
    "customer_id":   assigned_customers,
    "order_date":    [d.strftime("%Y-%m-%d") for d in order_dates],
    "status":        np.random.choice(ORDER_STATUSES, size=N_ORDERS, p=STATUS_WEIGHTS),
    "shipping_cost": np.round(np.random.choice(
        [0, 4.99, 7.99, 12.99, 19.99], size=N_ORDERS, p=[0.30, 0.25, 0.25, 0.12, 0.08]), 2),
})
orders_df.to_csv(os.path.join(OUTPUT_DIR, "orders.csv"), index=False)
print(f"  -> {len(orders_df):,} orders")


# Order Items
print("Generating order_items...")

item_rows = []
item_id   = 1
product_ids    = products_df["product_id"].tolist()
product_prices = dict(zip(products_df["product_id"], products_df["price"]))

for _, order in orders_df.iterrows():
    n_items = np.random.choice([1, 2, 3, 4, 5], p=[0.45, 0.30, 0.15, 0.07, 0.03])
    chosen  = random.sample(product_ids, min(n_items, len(product_ids)))
    for prod_id in chosen:
        base_price = product_prices[prod_id]
        quantity   = int(np.random.choice([1, 2, 3, 4], p=[0.60, 0.25, 0.10, 0.05]))
        discount   = round(random.choice([0, 0, 0, 0.05, 0.10, 0.15, 0.20]), 2)
        item_rows.append({
            "order_item_id": f"OI{str(item_id).zfill(7)}",
            "order_id":      order["order_id"],
            "product_id":    prod_id,
            "quantity":      quantity,
            "unit_price":    base_price,
            "discount":      discount,
        })
        item_id += 1

order_items_df = pd.DataFrame(item_rows)
order_items_df.to_csv(os.path.join(OUTPUT_DIR, "order_items.csv"), index=False)
print(f"  -> {len(order_items_df):,} order items")


# quick preview
print("\n--- customers.csv ---")
print(customers_out.head(5).to_string(index=False))

print("\n--- products.csv ---")
print(products_df.head(5).to_string(index=False))

print("\n--- orders.csv ---")
print(orders_df.head(5).to_string(index=False))

print("\n--- order_items.csv ---")
print(order_items_df.head(5).to_string(index=False))

print("\nDone. All CSVs written to ./data/")
