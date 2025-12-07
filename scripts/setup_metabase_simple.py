#!/usr/bin/env python3
"""
Setup Metabase dashboards with working queries - simplified version.
"""
import requests
import json
import time

METABASE_URL = "http://localhost:3000"
METABASE_API = f"{METABASE_URL}/api"
ADMIN_EMAIL = "admin@ecommerce.com"
ADMIN_PASSWORD = "EcommerceAdmin2025!"

session = requests.Session()

def login():
    """Login to Metabase."""
    resp = session.post(
        f"{METABASE_API}/session",
        json={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if resp.status_code == 200:
        token = resp.json().get("id")
        session.headers["X-Metabase-Session"] = token
        print(f"✅ Logged in")
        return True
    return False

def create_card(db_id, name, sql):
    """Create a simple card with native SQL query."""
    payload = {
        "name": name,
        "database_id": db_id,
        "dataset_query": {
            "type": "native",
            "native": {"query": sql},
            "database": db_id
        },
        "display": "table",
        "visualization_settings": {}
    }
    
    resp = session.post(f"{METABASE_API}/card", json=payload)
    if resp.status_code == 200:
        card_id = resp.json().get("id")
        print(f"✅ Card '{name}' created (ID: {card_id})")
        return card_id
    else:
        print(f"❌ Failed to create '{name}': {resp.text[:100]}")
        return None

def add_card_to_dashboard(dashboard_id, card_id, row=0, col=0):
    """Add a card to a dashboard."""
    payload = {
        "cards": [{"card_id": card_id, "sizeX": 4, "sizeY": 3, "row": row, "col": col}]
    }
    resp = session.put(f"{METABASE_API}/dashboard/{dashboard_id}", json=payload)
    return resp.status_code == 200

def main():
    print("\n🚀 Setting up Metabase Dashboards...\n")
    
    if not login():
        print("❌ Login failed")
        return
    
    # Database ID from previous setup (adjust if needed)
    db_id = 12
    
    # Dashboard IDs and their cards
    dashboards = {
        "Executive Dashboard": {
            "id": 12,
            "cards": [
                ("Total Revenue", "SELECT SUM(total_amount) as total_revenue FROM orders WHERE status = 'completed'"),
                ("Daily Revenue", "SELECT DATE(order_date) as date, SUM(total_amount) as revenue FROM orders WHERE status = 'completed' GROUP BY DATE(order_date) ORDER BY date DESC LIMIT 30"),
                ("Top Products", "SELECT p.name, SUM(oi.quantity * oi.price_at_time) as revenue FROM order_items oi JOIN products p ON oi.product_id = p.product_id JOIN orders o ON oi.order_id = o.order_id WHERE o.status = 'completed' GROUP BY p.product_id, p.name ORDER BY revenue DESC LIMIT 10"),
                ("Customer Geography", "SELECT u.country, COUNT(DISTINCT u.user_id) as customers FROM users u GROUP BY u.country ORDER BY customers DESC LIMIT 10")
            ]
        },
        "Customer Analytics": {
            "id": 13,
            "cards": [
                ("Total Customers", "SELECT COUNT(DISTINCT user_id) as total_customers FROM users"),
                ("Average Order Value", "SELECT ROUND(AVG(total_amount)::numeric, 2) as avg_order_value FROM orders WHERE status = 'completed'"),
                ("New Users (30 Days)", "SELECT DATE(signup_date) as cohort_date, COUNT(DISTINCT user_id) as new_users FROM users WHERE signup_date >= NOW() - INTERVAL '30 days' GROUP BY DATE(signup_date) ORDER BY cohort_date DESC"),
                ("Customers by Channel", "SELECT acquisition_channel, COUNT(DISTINCT user_id) as customers FROM users GROUP BY acquisition_channel ORDER BY customers DESC")
            ]
        },
        "Product Analytics": {
            "id": 14,
            "cards": [
                ("Total Products", "SELECT COUNT(DISTINCT product_id) as total_products FROM products"),
                ("Products by Category", "SELECT category, COUNT(*) as product_count FROM products GROUP BY category ORDER BY product_count DESC"),
                ("Top Selling Products", "SELECT p.name, SUM(oi.quantity) as units_sold FROM order_items oi JOIN products p ON oi.product_id = p.product_id GROUP BY p.product_id, p.name ORDER BY units_sold DESC LIMIT 10"),
                ("Category Pricing", "SELECT category, ROUND(AVG(price)::numeric, 2) as avg_price FROM products GROUP BY category ORDER BY avg_price DESC")
            ]
        }
    }
    
    for dashboard_name, dashboard_info in dashboards.items():
        print(f"\n📊 Setting up {dashboard_name}...")
        dashboard_id = dashboard_info["id"]
        col = 0
        row = 0
        
        for card_name, sql in dashboard_info["cards"]:
            card_id = create_card(db_id, card_name, sql)
            if card_id:
                add_card_to_dashboard(dashboard_id, card_id, row, col)
                col += 4
                if col >= 12:
                    col = 0
                    row += 3
    
    print("\n✅ Dashboard setup complete!")
    print(f"📈 Access Metabase at: {METABASE_URL}")

if __name__ == "__main__":
    main()
