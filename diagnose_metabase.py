#!/usr/bin/env python3
"""
Diagnose and fix Metabase database connection.
"""
import requests
import psycopg2

METABASE_API = "http://localhost:3000/api"

session = requests.Session()

# Login to Metabase
resp = session.post(f"{METABASE_API}/session", json={"username": "admin@ecommerce.com", "password": "EcommerceAdmin2025!"})
if resp.status_code != 200:
    print("❌ Metabase login failed")
    exit(1)

token = resp.json().get('id')
session.headers['X-Metabase-Session'] = token
print("✅ Logged into Metabase\n")

# Get all databases
resp = session.get(f"{METABASE_API}/database")
databases = resp.json()
db_list = databases.get('data', databases) if isinstance(databases, dict) else databases

print("📊 Databases in Metabase:")
for db in db_list:
    print(f"  ID: {db.get('id')}, Name: {db.get('name')}, Engine: {db.get('engine')}")
    
    # Check if it's a Postgres database
    if db.get('engine') == 'postgres':
        details = db.get('details', {})
        host = details.get('host')
        port = details.get('port')
        dbname = details.get('dbname')
        user = details.get('user')
        
        print(f"    Connection: {user}@{host}:{port}/{dbname}")
        
        # Try to connect directly and check tables
        try:
            conn = psycopg2.connect(
                host=host, port=port, database=dbname, user=user,
                password=details.get('password')
            )
            cursor = conn.cursor()
            cursor.execute("""SELECT table_name FROM information_schema.tables 
                            WHERE table_schema='public' ORDER BY table_name""")
            tables = cursor.fetchall()
            print(f"    Tables found: {len(tables)}")
            if tables:
                for t in tables:
                    print(f"      - {t[0]}")
            else:
                print("      ⚠️  NO TABLES FOUND!")
            conn.close()
        except Exception as e:
            print(f"    ❌ Connection error: {e}")
    print()

print("\n🔍 Saved Questions (Cards) in Metabase:")
resp = session.get(f"{METABASE_API}/card")
cards = resp.json()
card_list = cards.get('data', cards) if isinstance(cards, dict) else cards

for c in card_list[:10]:  # Show first 10
    print(f"  ID: {c.get('id')}, Name: {c.get('name')}, DB: {c.get('database_id')}")
