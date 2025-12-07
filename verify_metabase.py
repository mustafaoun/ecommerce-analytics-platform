#!/usr/bin/env python3
"""
Verify Metabase dashboards and their cards.
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

if resp.status_code == 200:
    token = resp.json().get("id")
    session.headers["X-Metabase-Session"] = token
    print("✅ Logged in\n")
    
    # Check dashboards
    for dashboard_id in [12, 13, 14]:
        resp = session.get(f"{METABASE_API}/dashboard/{dashboard_id}")
        if resp.status_code == 200:
            dashboard = resp.json()
            print(f"📊 Dashboard: {dashboard.get('name')} (ID: {dashboard_id})")
            
            cards = dashboard.get('dashcards', [])
            print(f"   Cards on dashboard: {len(cards)}")
            
            for card in cards:
                card_id = card.get('card_id')
                if card_id:
                    print(f"   - Card ID: {card_id}")
            print()
        else:
            print(f"❌ Failed to get dashboard {dashboard_id}: {resp.status_code}\n")
    
    # Check database connection
    print("\n🔗 Checking database connection...")
    resp = session.get(f"{METABASE_API}/database")
    if resp.status_code == 200:
        data = resp.json()
        databases = data.get('data', data) if isinstance(data, dict) else data
        if isinstance(databases, list):
            for db in databases:
                print(f"   Database: {db.get('name')} (ID: {db.get('id')}) - Enabled: {db.get('is_sample', False) == False}")
else:
    print("❌ Login failed")
