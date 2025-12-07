#!/usr/bin/env python3
"""
Fix Metabase database connection by updating host to use correct Docker network.
"""
import requests
import time

METABASE_API = "http://localhost:3000/api"

session = requests.Session()

# Login
resp = session.post(f"{METABASE_API}/session", json={"username": "admin@ecommerce.com", "password": "EcommerceAdmin2025!"})
token = resp.json().get('id')
session.headers['X-Metabase-Session'] = token
print("✅ Logged in\n")

# The issue: Metabase container can't reach 'ecommerce-postgres' because they're on different Docker networks
# Solution: Use the host IP or connect via a shared network. 
# Alternatively: recreate the connection using localhost:5432 via docker host

# First, let's delete the broken connection and recreate it with correct hostname
print("🔧 Checking database connections...\n")

# Get database ID 2 (Ecommerce Database)
resp = session.get(f"{METABASE_API}/database/2")
if resp.status_code == 200:
    db = resp.json()
    print(f"Current connection: {db.get('name')}")
    print(f"  Host: {db['details'].get('host')}")
    print(f"  Port: {db['details'].get('port')}")
    print(f"  DB: {db['details'].get('dbname')}\n")
    
    # Update the database connection to use 'host.docker.internal' for Windows Docker
    # or try the ecommerce-postgres container by checking if it's on same network
    new_details = db['details'].copy()
    
    # For Windows/Mac Docker Desktop: use host.docker.internal to reach host
    # For Linux: use 172.17.0.1 or check network
    # For Docker Compose on same network: should work as-is
    # Let's try 'localhost' with the mapped port
    
    new_details['host'] = 'localhost'
    new_details['port'] = 5432  # Make sure this matches the mapped port
    
    # Update via API
    update_payload = {
        "name": db.get('name'),
        "engine": "postgres",
        "details": new_details,
        "description": "Ecommerce database"
    }
    
    resp = session.put(f"{METABASE_API}/database/2", json=update_payload)
    if resp.status_code == 200:
        print("✅ Database connection updated to localhost:5432")
        print("   Waiting for Metabase to sync tables...\n")
        time.sleep(3)
        
        # Now trigger a sync
        resp = session.post(f"{METABASE_API}/database/2/sync_schema")
        print(f"✅ Schema sync triggered (status: {resp.status_code})\n")
        
        # Check tables
        time.sleep(2)
        resp = session.get(f"{METABASE_API}/database/2/metadata")
        if resp.status_code == 200:
            metadata = resp.json()
            tables = metadata.get('tables', [])
            print(f"📊 Tables now visible: {len(tables)}")
            for t in tables:
                print(f"  - {t.get('name')}")
        
    else:
        print(f"❌ Failed to update: {resp.status_code} {resp.text[:200]}")
else:
    print(f"❌ Database not found: {resp.status_code}")
