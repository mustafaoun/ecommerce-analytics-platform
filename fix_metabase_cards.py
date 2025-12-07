#!/usr/bin/env python3
"""
Properly add cards to Metabase dashboards.
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

# Card IDs from previous setup: 68-71, 72-75, 76-79
dashboard_cards = {
    12: [68, 69, 70, 71],  # Executive Dashboard
    13: [72, 73, 74, 75],  # Customer Analytics
    14: [76, 77, 78, 79]   # Product Analytics
}

for dashboard_id, card_ids in dashboard_cards.items():
    print(f"📊 Adding cards to dashboard {dashboard_id}...")
    
    # Get dashboard first
    resp = session.get(f"{METABASE_API}/dashboard/{dashboard_id}")
    if resp.status_code != 200:
        print(f"   ❌ Failed to get dashboard")
        continue
    
    dashboard = resp.json()
    
    # Build dashcards array with proper positioning
    dashcards = []
    col = 0
    row = 0
    
    for card_id in card_ids:
        dashcard = {
            "card_id": card_id,
            "row": row,
            "col": col,
            "sizeX": 4,
            "sizeY": 3,
            "parameter_mappings": [],
            "visualization_settings": {}
        }
        dashcards.append(dashcard)
        
        col += 4
        if col >= 12:
            col = 0
            row += 3
    
    # Update dashboard
    update_payload = {
        "dashcards": dashcards
    }
    
    resp = session.put(f"{METABASE_API}/dashboard/{dashboard_id}", json=update_payload)
    if resp.status_code == 200:
        print(f"   ✅ Added {len(card_ids)} cards to dashboard {dashboard_id}")
    else:
        print(f"   ❌ Failed to update dashboard: {resp.text[:200]}")

print("\n✅ Dashboard setup complete!")
