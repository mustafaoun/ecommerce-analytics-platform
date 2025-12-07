#!/usr/bin/env python3
"""
Setup Metabase with the ecommerce PostgreSQL database and create dashboards.
"""
import requests
import json
import time
import os
from typing import Dict, Any

METABASE_URL = "http://localhost:3000"
METABASE_API = f"{METABASE_URL}/api"
ADMIN_EMAIL = "admin@ecommerce.com"
ADMIN_PASSWORD = "EcommerceAdmin2025!"

# Database connection details
DB_HOST = os.getenv("DB_HOST", "ecommerce-postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "ecommerce")
DB_USER = os.getenv("DB_USER", "ecommerce_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ecommerce_password")

session = requests.Session()

def wait_for_metabase(max_retries=30):
    """Wait for Metabase to be ready."""
    for i in range(max_retries):
        try:
            resp = requests.get(f"{METABASE_URL}/api/health", timeout=5)
            if resp.status_code == 200:
                print("✅ Metabase is ready!")
                return True
        except Exception as e:
            print(f"⏳ Waiting for Metabase... ({i+1}/{max_retries})")
            time.sleep(2)
    print("❌ Metabase did not start in time")
    return False

def login(email: str, password: str) -> str:
    """Login to Metabase and return session token."""
    resp = session.post(
        f"{METABASE_API}/session",
        json={"username": email, "password": password}
    )
    if resp.status_code == 200:
        token = resp.json().get("id")
        session.headers["X-Metabase-Session"] = token
        print(f"✅ Logged in as {email}")
        return token
    else:
        print(f"❌ Login failed: {resp.text}")
        return None

def add_database() -> Dict[str, Any]:
    """Add the ecommerce PostgreSQL database to Metabase."""
    db_config = {
        "name": "Ecommerce DB",
        "engine": "postgres",
        "details": {
            "host": DB_HOST,
            "port": DB_PORT,
            "dbname": DB_NAME,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "ssl": False,
            "tunnel-enabled": False
        }
    }
    
    resp = session.post(f"{METABASE_API}/database", json=db_config)
    if resp.status_code == 200:
        db_info = resp.json()
        print(f"✅ Database added: {db_info.get('name')} (ID: {db_info.get('id')})")
        return db_info
    else:
        print(f"❌ Failed to add database: {resp.text}")
        return None

def get_databases() -> list:
    """Get list of all databases in Metabase."""
    resp = session.get(f"{METABASE_API}/database")
    if resp.status_code == 200:
        data = resp.json()
        # Handle case where response is a dict with 'data' key
        if isinstance(data, dict) and 'data' in data:
            return data['data']
        elif isinstance(data, list):
            return data
    return []

def create_collection(name: str) -> Dict[str, Any]:
    """Create a collection in Metabase."""
    resp = session.post(
        f"{METABASE_API}/collection",
        json={"name": name, "color": "#509ee3"}
    )
    if resp.status_code == 200:
        collection = resp.json()
        print(f"✅ Collection created: {name} (ID: {collection.get('id')})")
        return collection
    else:
        print(f"⚠️  Collection creation failed: {resp.text}")
        return None

def create_native_query(database_id: int, name: str, sql: str, collection_id: int = None, display: str = "table") -> Dict[str, Any]:
    """Create a native SQL query card in Metabase."""
    payload = {
        "name": name,
        "database_id": database_id,
        "dataset_query": {
            "type": "native",
            "native": {
                "query": sql
            },
            "database": database_id
        },
        "display": display,
        "description": name,
        "visualization_settings": {}
    }
    
    if collection_id:
        payload["collection_id"] = collection_id
    
    resp = session.post(f"{METABASE_API}/card", json=payload)
    if resp.status_code == 200:
        card = resp.json()
        print(f"✅ Card created: {name} (ID: {card.get('id')})")
        return card
    else:
        print(f"❌ Failed to create card '{name}': {resp.text}")
        return None

def create_dashboard(name: str, collection_id: int = None) -> Dict[str, Any]:
    """Create a dashboard."""
    payload = {
        "name": name,
        "description": name,
        "cta": None
    }
    
    if collection_id:
        payload["collection_id"] = collection_id
    
    resp = session.post(f"{METABASE_API}/dashboard", json=payload)
    if resp.status_code == 200:
        dashboard = resp.json()
        print(f"✅ Dashboard created: {name} (ID: {dashboard.get('id')})")
        return dashboard
    else:
        print(f"❌ Failed to create dashboard: {resp.text}")
        return None

def add_card_to_dashboard(dashboard_id: int, card_id: int) -> bool:
    """Add a card to a dashboard."""
    payload = {
        "cards": [
            {
                "card_id": card_id,
                "sizeX": 4,
                "sizeY": 3,
                "row": 0,
                "col": 0
            }
        ]
    }
    
    resp = session.put(f"{METABASE_API}/dashboard/{dashboard_id}", json=payload)
    if resp.status_code == 200:
        return True
    else:
        print(f"⚠️  Failed to add card: {resp.text}")
        return False

def main():
    print("\n🚀 Setting up Metabase with Ecommerce Database...\n")
    
    # Wait for Metabase to be ready
    if not wait_for_metabase():
        return
    
    # Login
    if not login(ADMIN_EMAIL, ADMIN_PASSWORD):
        return
    
    # Check if database already exists
    databases = get_databases()
    db_id = None
    for db in databases:
        if db.get("name") == "Ecommerce DB":
            db_id = db.get("id")
            print(f"✅ Using existing database (ID: {db_id})")
            break
    
    # Add database if it doesn't exist
    if not db_id:
        db = add_database()
        if db:
            db_id = db.get("id")
        else:
            print("❌ Could not add database")
            return
    
    # Create collection
    collection = create_collection("Ecommerce Analytics")
    collection_id = collection.get("id") if collection else None
    
    # Define dashboard configurations
    dashboards_config = [
        {
            "name": "Executive Dashboard",
            "cards": [
                {
                    "name": "Total Revenue",
                    "sql": """
                        SELECT SUM(total_amount) as total_revenue
                        FROM orders
                        WHERE status = 'completed'
                    """,
                    "display": "number"
                },
                {
                    "name": "Daily Revenue Trend",
                    "sql": """
                        SELECT DATE(order_date) as date, SUM(total_amount) as revenue, COUNT(*) as orders
                        FROM orders
                        WHERE status = 'completed'
                        GROUP BY DATE(order_date)
                        ORDER BY date DESC
                        LIMIT 30
                    """,
                    "display": "line"
                },
                {
                    "name": "Top Products by Revenue",
                    "sql": """
                        SELECT p.name, p.category, SUM(oi.quantity * oi.price_at_time) as revenue, SUM(oi.quantity) as units_sold
                        FROM order_items oi
                        JOIN products p ON oi.product_id = p.product_id
                        JOIN orders o ON oi.order_id = o.order_id
                        WHERE o.status = 'completed'
                        GROUP BY p.product_id, p.name, p.category
                        ORDER BY revenue DESC
                        LIMIT 10
                    """,
                    "display": "bar"
                },
                {
                    "name": "Customer Geography",
                    "sql": """
                        SELECT u.country, COUNT(DISTINCT u.user_id) as customers, SUM(o.total_amount) as revenue
                        FROM users u
                        LEFT JOIN orders o ON u.user_id = o.user_id
                        WHERE o.status = 'completed' OR o.order_id IS NULL
                        GROUP BY u.country
                        ORDER BY revenue DESC NULLS LAST
                    """,
                    "display": "table"
                }
            ]
        },
        {
            "name": "Customer Analytics",
            "cards": [
                {
                    "name": "Total Customers",
                    "sql": """
                        SELECT COUNT(DISTINCT user_id) as total_customers
                        FROM users
                    """,
                    "display": "number"
                },
                {
                    "name": "Average Order Value",
                    "sql": """
                        SELECT AVG(total_amount) as avg_order_value
                        FROM orders
                        WHERE status = 'completed'
                    """,
                    "display": "number"
                },
                {
                    "name": "Cohort Retention (Last 30 Days)",
                    "sql": """
                        SELECT DATE(signup_date) as cohort_date, COUNT(DISTINCT user_id) as new_users
                        FROM users
                        WHERE signup_date >= NOW() - INTERVAL '30 days'
                        GROUP BY DATE(signup_date)
                        ORDER BY cohort_date DESC
                    """,
                    "display": "line"
                },
                {
                    "name": "Customer by Acquisition Channel",
                    "sql": """
                        SELECT acquisition_channel, COUNT(DISTINCT user_id) as customers
                        FROM users
                        GROUP BY acquisition_channel
                        ORDER BY customers DESC
                    """,
                    "display": "pie"
                }
            ]
        },
        {
            "name": "Product Analytics",
            "cards": [
                {
                    "name": "Total Products",
                    "sql": """
                        SELECT COUNT(DISTINCT product_id) as total_products
                        FROM products
                    """,
                    "display": "number"
                },
                {
                    "name": "Products by Category",
                    "sql": """
                        SELECT category, COUNT(*) as product_count
                        FROM products
                        GROUP BY category
                        ORDER BY product_count DESC
                    """,
                    "display": "bar"
                },
                {
                    "name": "Top Selling Products",
                    "sql": """
                        SELECT p.name, SUM(oi.quantity) as units_sold, SUM(oi.quantity * oi.price_at_time) as revenue
                        FROM order_items oi
                        JOIN products p ON oi.product_id = p.product_id
                        GROUP BY p.product_id, p.name
                        ORDER BY units_sold DESC
                        LIMIT 15
                    """,
                    "display": "bar"
                },
                {
                    "name": "Average Price by Category",
                    "sql": """
                        SELECT category, AVG(price) as avg_price, COUNT(*) as product_count
                        FROM products
                        GROUP BY category
                        ORDER BY avg_price DESC
                    """,
                    "display": "table"
                }
            ]
        }
    ]
    
    # Create dashboards and cards
    for dashboard_config in dashboards_config:
        dashboard = create_dashboard(dashboard_config["name"], collection_id)
        if not dashboard:
            continue
        
        dashboard_id = dashboard.get("id")
        row = 0
        col = 0
        
        for idx, card_config in enumerate(dashboard_config["cards"]):
            card = create_native_query(
                db_id,
                card_config["name"],
                card_config["sql"],
                collection_id,
                card_config.get("display", "table")
            )
            
            if card:
                card_id = card.get("id")
                # Add card to dashboard with positioning
                payload = {
                    "cards": [
                        {
                            "card_id": card_id,
                            "sizeX": 4,
                            "sizeY": 3,
                            "row": row,
                            "col": col
                        }
                    ]
                }
                
                resp = session.put(f"{METABASE_API}/dashboard/{dashboard_id}", json=payload)
                
                # Update position for next card
                col += 4
                if col >= 12:
                    col = 0
                    row += 3
    
    print("\n✅ Metabase setup complete!")
    print(f"📊 Access Metabase at: {METABASE_URL}")
    print(f"📈 Dashboards created in collection: Ecommerce Analytics")

if __name__ == "__main__":
    main()
