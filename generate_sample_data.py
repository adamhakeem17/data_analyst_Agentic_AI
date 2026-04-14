"""Generate a 500-row demo sales CSV so users can try the app immediately."""

import os

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)
N = 500

REGIONS = ["North", "South", "East", "West", "Central"]
PRODUCTS = ["Laptop Pro", "Wireless Mouse", "USB-C Hub", "Monitor 27\"",
            "Mechanical Keyboard", "Webcam HD", "SSD 1TB", "RAM 16GB"]
CATEGORIES = {
    "Laptop Pro": "Computers", "Wireless Mouse": "Peripherals",
    "USB-C Hub": "Accessories", "Monitor 27\"": "Displays",
    "Mechanical Keyboard": "Peripherals", "Webcam HD": "Accessories",
    "SSD 1TB": "Storage", "RAM 16GB": "Storage",
}
CHANNELS = ["Online", "Retail", "B2B", "Partner"]
UNIT_PRICES = {
    "Laptop Pro": 1299, "Wireless Mouse": 49, "USB-C Hub": 79,
    "Monitor 27\"": 449, "Mechanical Keyboard": 129, "Webcam HD": 89,
    "SSD 1TB": 119, "RAM 16GB": 69,
}

start = datetime(2024, 1, 1)
dates = [start + timedelta(days=int(d)) for d in np.random.randint(0, 365, N)]
products = np.random.choice(PRODUCTS, N)
quantities = np.random.randint(1, 20, N)
prices = np.array([UNIT_PRICES[p] for p in products])
discounts = np.round(np.random.choice([0, 0.05, 0.10, 0.15, 0.20], N), 2)
revenue = np.round(quantities * prices * (1 - discounts), 2)

df = pd.DataFrame({
    "order_id": [f"ORD-{10000 + i}" for i in range(N)],
    "date": [d.strftime("%Y-%m-%d") for d in dates],
    "region": np.random.choice(REGIONS, N),
    "channel": np.random.choice(CHANNELS, N),
    "product": products,
    "category": [CATEGORIES[p] for p in products],
    "quantity": quantities,
    "unit_price": prices,
    "discount": discounts,
    "revenue": revenue,
    "customer_id": [f"CUST-{np.random.randint(1000, 9999)}" for _ in range(N)],
})

os.makedirs("sample_data", exist_ok=True)
df.to_csv("sample_data/sales_sample.csv", index=False)
print(f"Wrote sample_data/sales_sample.csv ({N} rows)")
print(df.head())
