import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
n = 1000

dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n)]
categories = ['Electronics', 'Clothing', 'Food', 'Furniture', 'Accessories']
regions = ['Jakarta', 'Surabaya', 'Bandung', 'Medan', 'Makassar']
payment = ['Cash', 'Credit Card', 'Transfer', 'E-Wallet']

df = pd.DataFrame({
    'Date': dates,
    'Product': [random.choice(['Laptop','Mouse','Keyboard','Phone','Tablet','Shirt','Pants','Rice','Chair','Desk']) for _ in range(n)],
    'Category': [random.choice(categories) for _ in range(n)],
    'Region': [random.choice(regions) for _ in range(n)],
    'Payment_Method': [random.choice(payment) for _ in range(n)],
    'Sales': np.random.normal(50000, 15000, n).round(2),
    'Quantity': np.random.randint(1, 20, n),
    'Discount': np.random.uniform(0, 0.3, n).round(2),
    'Profit': np.random.normal(15000, 5000, n).round(2),
})

df.loc[random.sample(range(n), 10), 'Sales'] = np.nan
df.loc[random.sample(range(n), 5), 'Profit'] = np.nan

df.to_csv('sales_data.csv', index=False)
df.to_excel('sales_data.xlsx', index=False)
print("Dataset berhasil dibuat!")
print(df.head())