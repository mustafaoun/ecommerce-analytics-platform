#!/usr/bin/env python3
"""
Create three automated dashboards in Metabase and attach saved queries (cards) by name.
These dashboards will automatically reflect regenerated data because they reference the underlying
saved queries which run live against the connected Postgres DB.

Usage: python create_automated_dashboards.py
"""
import requests
import time

METABASE_URL = "http://localhost:3000"
API = f"{METABASE_URL}/api"
ADMIN_EMAIL = "admin@ecommerce.com"
ADMIN_PASSWORD = "EcommerceAdmin2025!"

session = requests.Session()

def login():
    r = session.post(f"{API}/session", json={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if r.status_code == 200:
        session.headers["X-Metabase-Session"] = r.json().get("id")
        print("✅ Logged in to Metabase")
        return True
    print("❌ Login failed", r.text)
    return False


def find_card_by_name(name):
    """Return card id for a given card name (or None)."""
    r = session.get(f"{API}/card")
    if r.status_code != 200:
        print("Failed to list cards", r.status_code)
        return None
    cards = r.json()
    # API may return {data: [...]} or a list
    if isinstance(cards, dict) and 'data' in cards:
        cards = cards['data']
    for c in cards:
        if c.get('name') == name:
            return c.get('id')
    return None


def create_dashboard(name, description=None):
    payload = {"name": name}
    if description:
        payload['description'] = description
    r = session.post(f"{API}/dashboard", json=payload)
    if r.status_code == 200:
        dash = r.json()
        print(f"✅ Created dashboard '{name}' (ID: {dash.get('id')})")
        return dash.get('id')
    print(f"❌ Failed to create dashboard '{name}'", r.status_code, r.text[:200])
    return None


def add_card_to_dashboard(dashboard_id, card_id, row=0, col=0, sizeX=6, sizeY=4):
    """Add a card to a dashboard using the correct field names (cardId camelCase).
    Uses POST /api/dashboard/{dashboard_id}/cards payload {cardId, row, col, sizeX, sizeY}
    """
    payload = {
        "cardId": card_id,
        "row": row,
        "col": col,
        "sizeX": sizeX,
        "sizeY": sizeY,
    }
    r = session.post(f"{API}/dashboard/{dashboard_id}/cards", json=payload)
    if r.status_code in (200, 201):
        print(f"   ✅ Added card {card_id} to dashboard {dashboard_id}")
        return True
    print(f"   ⚠️  Failed to add card {card_id} -> status {r.status_code}; body: {r.text[:300]}")
    return False


def ensure_saved_queries_exist(names_and_sql, db_id=None):
    """Ensure saved queries (cards) exist; create them if missing. Returns mapping name->card_id."""
    mapping = {}
    for name, sql in names_and_sql.items():
        cid = find_card_by_name(name)
        if cid:
            mapping[name] = cid
            print(f"Found existing card '{name}' (ID: {cid})")
            continue
        # create card
        payload = {
            "name": name,
            "dataset_query": {
                "type": "native",
                "native": {"query": sql},
                # If db_id is provided, include it, else Metabase uses default DB
                **({'database': db_id} if db_id else {})
            },
            "display": "table",
            "visualization_settings": {}
        }
        r = session.post(f"{API}/card", json=payload)
        if r.status_code == 200:
            created = r.json()
            mapping[name] = created.get('id')
            print(f"Created card '{name}' (ID: {created.get('id')})")
        else:
            print(f"Failed to create card '{name}': {r.status_code} {r.text[:200]}")
    return mapping


def main():
    if not login():
        return

    # Define saved queries (these mirror the queries used previously)
    saved_queries = {
        "Total Revenue": "SELECT SUM(total_amount)::numeric(12,2) as total_revenue FROM orders WHERE status = 'completed'",
        "Daily Revenue": "SELECT DATE(order_date) as date, SUM(total_amount)::numeric(12,2) as revenue FROM orders WHERE status = 'completed' GROUP BY DATE(order_date) ORDER BY date DESC LIMIT 30",
        "Top Products": "SELECT p.name, SUM(oi.quantity * oi.price_at_time)::numeric(12,2) as revenue FROM order_items oi JOIN products p ON oi.product_id = p.product_id JOIN orders o ON oi.order_id = o.order_id WHERE o.status = 'completed' GROUP BY p.product_id, p.name ORDER BY revenue DESC LIMIT 10",
        "Customer Geography": "SELECT u.country, COUNT(DISTINCT u.user_id) as customers, SUM(o.total_amount) as revenue FROM users u LEFT JOIN orders o ON u.user_id = o.user_id WHERE o.status = 'completed' OR o.order_id IS NULL GROUP BY u.country ORDER BY revenue DESC NULLS LAST",
        "Total Customers": "SELECT COUNT(DISTINCT user_id) as total_customers FROM users",
        "Average Order Value": "SELECT ROUND(AVG(total_amount)::numeric, 2) as avg_order_value FROM orders WHERE status = 'completed'",
        "Products by Category": "SELECT category, COUNT(*) as product_count FROM products GROUP BY category ORDER BY product_count DESC",
        "Top Selling Products": "SELECT p.name, SUM(oi.quantity) as units_sold, SUM(oi.quantity * oi.price_at_time) as revenue FROM order_items oi JOIN products p ON oi.product_id = p.product_id GROUP BY p.product_id, p.name ORDER BY units_sold DESC LIMIT 15",
    }

    # Ensure cards exist; Metabase will use the default DB unless the saved card specifies database.
    name_to_card = ensure_saved_queries_exist(saved_queries)

    # Dashboard definitions: name -> ordered list of card names
    dashboards = {
        "Executive Dashboard": ["Total Revenue", "Daily Revenue", "Top Products", "Customer Geography"],
        "Customer Analytics": ["Total Customers", "Average Order Value", "Customer Geography", "Products by Category"],
        "Product Analytics": ["Products by Category", "Top Selling Products", "Top Products", "Total Revenue"],
    }

    # Create dashboards and attach cards
    for dname, card_names in dashboards.items():
        dash_id = create_dashboard(dname, description=f"Automated dashboard: {dname}")
        if not dash_id:
            print(f"Skipping dashboard {dname}")
            continue
        col = 0
        row = 0
        for cn in card_names:
            cid = name_to_card.get(cn)
            if not cid:
                print(f"No card found for '{cn}', skipping")
                continue
            added = add_card_to_dashboard(dash_id, cid, row=row, col=col)
            # Advance layout
            col += 6
            if col >= 12:
                col = 0
                row += 4
        time.sleep(0.5)

    print("\n✅ Automated dashboards created or updated. They run live against the DB, so regenerating data will update the insights.")

if __name__ == '__main__':
    main()
