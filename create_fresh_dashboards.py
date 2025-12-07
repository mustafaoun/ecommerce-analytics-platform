#!/usr/bin/env python3
"""
Create complete Metabase dashboards with cards from scratch.
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

if resp.status_code != 200:
    print("❌ Login failed")
    exit(1)

token = resp.json().get("id")
session.headers["X-Metabase-Session"] = token
print("✅ Logged in\n")

# Get database ID
resp = session.get(f"{METABASE_API}/database")
databases = resp.json()
db_data = databases.get('data', databases) if isinstance(databases, dict) else databases

db_id = None
for db in db_data if isinstance(db_data, list) else []:
    if db.get('name') == 'Ecommerce DB':
        db_id = db.get('id')
        break

if not db_id:
    print("❌ Ecommerce DB not found")
    exit(1)

print(f"✅ Using database ID: {db_id}\n")

# Dashboard configurations
dashboards_config = [
    {
        "name": "Executive Summary",
        "cards": [
            ("Total Revenue", "SELECT SUM(total_amount)::money as total_revenue FROM orders WHERE status = 'completed'"),
            ("Daily Revenue", "SELECT DATE(order_date) as date, SUM(total_amount) as revenue FROM orders WHERE status = 'completed' GROUP BY DATE(order_date) ORDER BY date DESC LIMIT 30"),
            ("Top Products", "SELECT p.name, SUM(oi.quantity * oi.price_at_time) as revenue FROM order_items oi JOIN products p ON oi.product_id = p.product_id JOIN orders o ON oi.order_id = o.order_id WHERE o.status = 'completed' GROUP BY p.product_id, p.name ORDER BY revenue DESC LIMIT 10"),
            ("Orders by Status", "SELECT status, COUNT(*) as count FROM orders GROUP BY status"),
        ]
    },
    {
        "name": "Customer Insights",
        "cards": [
            ("Total Customers", "SELECT COUNT(DISTINCT user_id) as total_customers FROM users"),
            ("Average Order Value", "SELECT ROUND(AVG(total_amount)::numeric, 2) as avg_order_value FROM orders WHERE status = 'completed'"),
            ("Repeat Customers", "SELECT COUNT(DISTINCT user_id) as repeat_customers FROM (SELECT user_id FROM orders WHERE status = 'completed' GROUP BY user_id HAVING COUNT(*) > 1) t"),
            ("Top Countries", "SELECT u.country, COUNT(DISTINCT u.user_id) as customers FROM users u GROUP BY u.country ORDER BY customers DESC LIMIT 10"),
        ]
    },
    {
        "name": "Product Performance",
        "cards": [
            ("Total Products", "SELECT COUNT(*) as total_products FROM products"),
            ("Products by Category", "SELECT category, COUNT(*) as product_count FROM products GROUP BY category ORDER BY product_count DESC"),
            ("Best Sellers", "SELECT p.name, SUM(oi.quantity) as units_sold, SUM(oi.quantity * oi.price_at_time) as revenue FROM order_items oi JOIN products p ON oi.product_id = p.product_id GROUP BY p.product_id, p.name ORDER BY units_sold DESC LIMIT 10"),
            ("Inventory Value", "SELECT category, ROUND(AVG(price)::numeric, 2) as avg_price, COUNT(*) as count FROM products GROUP BY category ORDER BY avg_price DESC"),
        ]
    }
]

# Delete old dashboards first
for dashboard_id in [12, 13, 14]:
    resp = session.delete(f"{METABASE_API}/dashboard/{dashboard_id}")
    if resp.status_code == 204:
        print(f"🗑️  Deleted old dashboard {dashboard_id}")

print("\n🚀 Creating new dashboards...\n")

# Create new dashboards with cards
for dashboard_config in dashboards_config:
    dashboard_name = dashboard_config["name"]
    
    # Create dashboard
    dashboard_payload = {
        "name": dashboard_name,
        "description": dashboard_name,
        "parameters": [],
        "enable_caching": False
    }
    
    resp = session.post(f"{METABASE_API}/dashboard", json=dashboard_payload)
    if resp.status_code != 200:
        print(f"❌ Failed to create dashboard '{dashboard_name}'")
        continue
    
    dashboard = resp.json()
    dashboard_id = dashboard.get('id')
    print(f"✅ Dashboard '{dashboard_name}' created (ID: {dashboard_id})")
    
    # Add cards to dashboard
    col = 0
    row = 0
    
    for card_name, sql in dashboard_config["cards"]:
        # Create card
        card_payload = {
            "name": card_name,
            "database_id": db_id,
            "dataset_query": {
                "type": "native",
                "native": {"query": sql},
                "database": db_id
            },
            "display": "table",
            "visualization_settings": {},
            "description": card_name
        }
        
        resp = session.post(f"{METABASE_API}/card", json=card_payload)
        if resp.status_code != 200:
            print(f"   ❌ Failed to create card '{card_name}'")
            continue
        
        card = resp.json()
        card_id = card.get('id')
        print(f"   ✅ Card '{card_name}' created (ID: {card_id})")
        
        # Add card to dashboard
        dashcard_payload = {
            "card_id": card_id,
            "row": row,
            "col": col,
            "sizeX": 6,
            "sizeY": 4,
            "parameter_mappings": [],
            "visualization_settings": {}
        }
        
        resp = session.post(f"{METABASE_API}/dashboard/{dashboard_id}/cards", json=dashcard_payload)
        if resp.status_code == 200:
            print(f"      ✅ Added to dashboard")
        else:
            print(f"      ⚠️  Card created but add to dashboard failed: {resp.status_code}")
        
        col += 6
        if col >= 12:
            col = 0
            row += 4

print("\n🎉 Dashboard setup complete!")
print(f"📊 Open Metabase: {METABASE_URL}")
