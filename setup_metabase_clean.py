
#!/usr/bin/env python3
"""
Complete Metabase setup - add database and create queries.
"""
import requests
import json
import time

METABASE_URL = "http://localhost:3000"
METABASE_API = f"{METABASE_URL}/api"
ADMIN_EMAIL = "admin@ecommerce.com"
ADMIN_PASSWORD = "EcommerceAdmin2025!"

DB_HOST = "ecommerce-postgres"
DB_PORT = 5432
DB_NAME = "ecommerce"
DB_USER = "ecommerce_user"
DB_PASSWORD = "ecommerce_password"

session = requests.Session()

def wait_for_metabase():
    for i in range(120):
        try:
            resp = requests.get(f"{METABASE_URL}/api/health", timeout=5)
            if resp.status_code == 200:
                print("✅ Metabase is ready")
                return True
        except:
            pass
        if i % 10 == 0:
            print(f"⏳ Waiting for Metabase... ({i+1}/120)")
        time.sleep(1)
    return False

def login():
    resp = session.post(
        f"{METABASE_API}/session",
        json={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if resp.status_code == 200:
        token = resp.json().get("id")
        session.headers["X-Metabase-Session"] = token
        print("✅ Logged in")
        return True
    return False

def add_database():
    config = {
        "name": "Ecommerce Database",
        "engine": "postgres",
        "details": {
            "host": DB_HOST,
            "port": DB_PORT,
            "dbname": DB_NAME,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "ssl": False
        }
    }
    
    resp = session.post(f"{METABASE_API}/database", json=config)
    if resp.status_code == 200:
        db_id = resp.json().get("id")
        print(f"✅ Database added (ID: {db_id})")
        return db_id
    return None

def create_query_card(db_id, title, sql):
    """Create a query card that can be used in dashboards."""
    payload = {
        "name": title,
        "dataset_query": {
            "database": db_id,
            "type": "native",
            "native": {
                "query": sql
            }
        },
        "display": "table",
        "description": title,
        "visualization_settings": {}
    }
    
    resp = session.post(f"{METABASE_API}/card", json=payload)
    if resp.status_code == 200:
        card_id = resp.json().get("id")
        print(f"   ✅ Query '{title}' created (ID: {card_id})")
        return card_id
    else:
        print(f"   ❌ Failed: {resp.status_code}")
        return None

print("\n🚀 Setting up Metabase...\n")

if not wait_for_metabase():
    print("❌ Metabase failed to start")
    exit(1)

if not login():
    print("❌ Login failed")
    exit(1)

db_id = add_database()
if not db_id:
    print("❌ Failed to add database")
    exit(1)

print("\n📊 Creating saved queries...\n")

queries = [
    ("Total Revenue", "SELECT SUM(total_amount)::numeric(12,2) as revenue FROM orders WHERE status = 'completed'"),
    ("Daily Revenue", "SELECT DATE(order_date) as date, SUM(total_amount)::numeric(12,2) as revenue FROM orders WHERE status = 'completed' GROUP BY DATE(order_date) ORDER BY date DESC LIMIT 30"),
    ("Top Products", "SELECT p.name, SUM(oi.quantity * oi.price_at_time)::numeric(12,2) as revenue FROM order_items oi JOIN products p ON oi.product_id = p.product_id JOIN orders o ON oi.order_id = o.order_id WHERE o.status = 'completed' GROUP BY p.product_id, p.name ORDER BY revenue DESC LIMIT 10"),
    ("Orders Status", "SELECT status, COUNT(*) as count FROM orders GROUP BY status"),
    ("Total Customers", "SELECT COUNT(DISTINCT user_id) as total FROM users"),
    ("Avg Order Value", "SELECT ROUND(AVG(total_amount)::numeric, 2) as value FROM orders WHERE status = 'completed'"),
    ("Product Categories", "SELECT category, COUNT(*) as count FROM products GROUP BY category"),
    ("Top Countries", "SELECT u.country, COUNT(DISTINCT u.user_id) as customers FROM users u GROUP BY u.country ORDER BY customers DESC LIMIT 10"),
]

card_ids = []
for title, sql in queries:
    card_id = create_query_card(db_id, title, sql)
    if card_id:
        card_ids.append(card_id)

print(f"\n✅ Setup complete!")
print(f"📊 Open Metabase: {METABASE_URL}")
print(f"📊 Dashboards can be created manually at: {METABASE_URL}/dashboard/new")
print(f"\n💡 Tip: Use 'New' button to create dashboards and add these saved queries as cards")
