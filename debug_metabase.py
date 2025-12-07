#!/usr/bin/env python3
"""
Debug Metabase API - check dashboard structure and correct endpoints.
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

# Get dashboard 15
resp = session.get(f"{METABASE_API}/dashboard/15")
if resp.status_code == 200:
    dashboard = resp.json()
    print("Dashboard structure:")
    print(json.dumps(dashboard, indent=2, default=str)[:2000])
    print("\n...\n")
    
    # Check what fields are available
    print("\nKey fields in dashboard:")
    for key in ['id', 'name', 'dashcards', 'parameters', 'caching_ttl', 'enable_caching']:
        if key in dashboard:
            print(f"  {key}: present")
else:
    print(f"Failed to get dashboard: {resp.status_code}")
