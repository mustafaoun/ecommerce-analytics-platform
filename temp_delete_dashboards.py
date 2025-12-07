import requests

session = requests.Session()

# Login first
resp = session.post(
    "http://localhost:3000/api/session",
    json={"username": "admin@ecommerce.com", "password": "EcommerceAdmin2025!"}
)
if resp.status_code == 200:
    token = resp.json().get("id")
    session.headers["X-Metabase-Session"] = token
    print("Logged in")
    
    # Delete dashboards 12, 13, 14
    for dashboard_id in [12, 13, 14]:
        resp = session.delete(f"http://localhost:3000/api/dashboard/{dashboard_id}")
        print(f"Deleted dashboard {dashboard_id}: {resp.status_code}")
else:
    print("Login failed")
