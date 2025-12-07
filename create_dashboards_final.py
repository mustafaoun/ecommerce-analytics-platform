#!/usr/bin/env python3
"""
Create Metabase dashboards with saved queries.
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

# Define dashboards with their query IDs
dashboards = {
    "Executive Summary": [148, 149, 150, 151],  # Revenue, Daily Revenue, Top Products, Orders Status
    "Customer Analytics": [152, 153, 155, 154],  # Total Customers, AOV, Top Countries, Categories
}

print("🚀 Creating dashboards...\n")

for dashboard_name, query_ids in dashboards.items():
    # Create dashboard
    dashboard_payload = {
        "name": dashboard_name,
        "description": dashboard_name,
        "caching_ttl": None,
        "enable_caching": False
    }
    
    resp = session.post(f"{METABASE_API}/dashboard", json=dashboard_payload)
    if resp.status_code != 200:
        print(f"❌ Failed to create dashboard '{dashboard_name}'")
        continue
    
    dashboard_id = resp.json().get("id")
    print(f"✅ Dashboard '{dashboard_name}' created (ID: {dashboard_id})")
    
    # Add queries as cards to the dashboard
    for idx, query_id in enumerate(query_ids):
        # Create a dashcard entry
        dashcard = {
            "card_id": query_id,
            "row": (idx // 2) * 4,
            "col": (idx % 2) * 6,
            "sizeX": 6,
            "sizeY": 4,
            "parameter_mappings": [],
            "visualization_settings": {}
        }
        
        # Add card to dashboard - use the correct endpoint
        resp = session.post(
            f"{METABASE_API}/dashboard/{dashboard_id}/dashcards",
            json=dashcard
        )
        
        if resp.status_code in [200, 201]:
            print(f"   ✅ Added query {query_id}")
        else:
            print(f"   ⚠️  Status {resp.status_code} for query {query_id}")

print("\n✅ Dashboard creation complete!")
print(f"📊 Open Metabase: {METABASE_URL}")
print(f"📈 Your dashboards are ready to view!")
