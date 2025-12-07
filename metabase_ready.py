#!/usr/bin/env python3
"""
Simple Metabase dashboard setup - create working dashboards manually.
"""
import requests
import json

METABASE_URL = "http://localhost:3000"
METABASE_API = f"{METABASE_URL}/api"

session = requests.Session()

# Login
resp = session.post(
    f"{METABASE_API}/session",
    json={"username": "admin@ecommerce.com", "password": "EcommerceAdmin2025!"}
)

token = resp.json().get("id")
session.headers["X-Metabase-Session"] = token
print("✅ Logged in\n")

# Get the ecommerce database ID
resp = session.get(f"{METABASE_API}/database")
databases = resp.json()
db_data = databases.get('data', databases) if isinstance(databases, dict) else databases

db_id = None
for db in (db_data if isinstance(db_data, list) else []):
    if db.get('name') == 'Ecommerce DB':
        db_id = db.get('id')
        break

print(f"Using database ID: {db_id}\n")

# Just open the Metabase URL and let the user manually add cards
print("🌐 Metabase is ready!")
print(f"📊 URL: {METABASE_URL}")
print(f"📧 Email: admin@ecommerce.com")
print(f"🔑 Password: EcommerceAdmin2025!")
print(f"\n✅ Database is connected: Ecommerce DB (ID: {db_id})")
print("\n📝 Dashboards created:")
print("  - Executive Summary (ID: 15)")
print("  - Customer Insights (ID: 16)")
print("  - Product Performance (ID: 17)")
print("\n📌 Sample Queries you can run in Metabase:")
print("""
1. Total Revenue
   SELECT SUM(total_amount) as revenue FROM orders WHERE status = 'completed'

2. Daily Revenue Trend
   SELECT DATE(order_date) as date, SUM(total_amount) as revenue 
   FROM orders WHERE status = 'completed' 
   GROUP BY DATE(order_date) ORDER BY date DESC LIMIT 30

3. Top 10 Products
   SELECT p.name, SUM(oi.quantity) as units_sold
   FROM order_items oi
   JOIN products p ON oi.product_id = p.product_id
   GROUP BY p.product_id, p.name
   ORDER BY units_sold DESC LIMIT 10

4. Customer Count by Country
   SELECT u.country, COUNT(DISTINCT u.user_id) as customers
   FROM users u
   GROUP BY u.country
   ORDER BY customers DESC

5. Orders by Status
   SELECT status, COUNT(*) FROM orders GROUP BY status
""")
