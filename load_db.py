"""
load_db.py

Reads the 4 CSVs from /data and loads them into a SQLite database.
Run after generate_data.py.
"""

import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH  = os.path.join(DATA_DIR, "revenuelens.db")

print("Loading CSVs...")
customers   = pd.read_csv(os.path.join(DATA_DIR, "customers.csv"))
products    = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))
orders      = pd.read_csv(os.path.join(DATA_DIR, "orders.csv"))
order_items = pd.read_csv(os.path.join(DATA_DIR, "order_items.csv"))

print(f"Writing to {DB_PATH}...")
con = sqlite3.connect(DB_PATH)
cur = con.cursor()

cur.executescript("""
PRAGMA journal_mode=WAL;

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;

CREATE TABLE customers (
    customer_id  TEXT PRIMARY KEY,
    name         TEXT,
    email        TEXT,
    signup_date  TEXT,
    region       TEXT,
    segment      TEXT
);

CREATE TABLE products (
    product_id   TEXT PRIMARY KEY,
    name         TEXT,
    category     TEXT,
    sub_category TEXT,
    price        REAL,
    cost         REAL
);

CREATE TABLE orders (
    order_id      TEXT PRIMARY KEY,
    customer_id   TEXT REFERENCES customers(customer_id),
    order_date    TEXT,
    status        TEXT,
    shipping_cost REAL
);

CREATE TABLE order_items (
    order_item_id TEXT PRIMARY KEY,
    order_id      TEXT REFERENCES orders(order_id),
    product_id    TEXT REFERENCES products(product_id),
    quantity      INTEGER,
    unit_price    REAL,
    discount      REAL
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date     ON orders(order_date);
CREATE INDEX idx_items_order     ON order_items(order_id);
CREATE INDEX idx_items_product   ON order_items(product_id);
""")

customers.to_sql("customers",     con, if_exists="append", index=False)
products.to_sql("products",       con, if_exists="append", index=False)
orders.to_sql("orders",           con, if_exists="append", index=False)
order_items.to_sql("order_items", con, if_exists="append", index=False)

con.commit()
con.close()

# sanity check
con = sqlite3.connect(DB_PATH)
for tbl in ["customers", "products", "orders", "order_items"]:
    n = pd.read_sql(f"SELECT COUNT(*) AS n FROM {tbl}", con).iloc[0, 0]
    print(f"  {tbl}: {n:,} rows")
con.close()

print("Done.")
