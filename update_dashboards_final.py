#!/usr/bin/env python3
"""
Properly add cards to dashboards by updating the dashboard object.
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

# Card assignments: dashboard_id -> [card_ids]
assignments = {
    15: [80, 81, 82, 83],      # Executive Summary
    16: [84, 85, 86, 87],      # Customer Insights
    17: [88, 89, 90, 91]       # Product Performance
}

for dashboard_id, card_ids in assignments.items():
    print(f"📊 Updating dashboard {dashboard_id}...")
    
    # Get current dashboard
    resp = session.get(f"{METABASE_API}/dashboard/{dashboard_id}")
    if resp.status_code != 200:
        print(f"   ❌ Failed to get dashboard")
        continue
    
    dashboard = resp.json()
    
    # Build dashcards
    dashcards = []
    col = 0
    row = 0
    
    for card_id in card_ids:
        dashcard = {
            "card_id": card_id,
            "row": row,
            "col": col,
            "sizeX": 6,
            "sizeY": 4,
            "series": [],
            "visualization_settings": {},
            "parameter_mappings": []
        }
        dashcards.append(dashcard)
        
        col += 6
        if col >= 12:
            col = 0
            row += 4
    
    # Update dashboard with dashcards
    update_payload = {"dashcards": dashcards}
    
    resp = session.put(f"{METABASE_API}/dashboard/{dashboard_id}", json=update_payload)
    
    if resp.status_code == 200:
        print(f"   ✅ Updated with {len(card_ids)} cards")
        result = resp.json()
        print(f"      Dashboard now has {len(result.get('dashcards', []))} cards")
    else:
        print(f"   ❌ Failed: {resp.status_code}")
        print(f"      {resp.text[:200]}")

print("\n✅ Dashboard update complete!")
