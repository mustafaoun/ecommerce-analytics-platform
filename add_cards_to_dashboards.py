#!/usr/bin/env python3
"""
Add existing cards to dashboards using correct Metabase API.
"""
import requests

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
    print(f"📊 Adding cards to dashboard {dashboard_id}...")
    
    col = 0
    row = 0
    
    for card_id in card_ids:
        # Use correct endpoint: POST /dashboard/{id}/cards
        dashcard_payload = {
            "card_id": card_id,
            "row": row,
            "col": col,
            "sizeX": 6,
            "sizeY": 4
        }
        
        resp = session.post(
            f"{METABASE_URL}/api/dashboard/{dashboard_id}/cards",
            json=dashcard_payload
        )
        
        if resp.status_code == 200:
            print(f"   ✅ Card {card_id} added")
        else:
            print(f"   Status: {resp.status_code}")
        
        col += 6
        if col >= 12:
            col = 0
            row += 4

print("\n✅ All cards added to dashboards!")
