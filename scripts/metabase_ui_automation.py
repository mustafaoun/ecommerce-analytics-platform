#!/usr/bin/env python3
"""
UI automation to add saved questions to Metabase dashboards using Playwright.

Requires: playwright (`pip install playwright`) and `playwright install` to install browsers.

This script:
- Logs into Metabase
- For each dashboard name, opens the dashboard in edit mode
- Clicks "Add a question" -> selects the saved question by name -> adds it to the dashboard

Note: Metabase UI changes across versions; selectors may need adjustment.
"""
import time
import requests
from playwright.sync_api import sync_playwright

METABASE_URL = "http://localhost:3000"
API = f"{METABASE_URL}/api"
ADMIN_EMAIL = "admin@ecommerce.com"
ADMIN_PASSWORD = "EcommerceAdmin2025!"

# Dashboards and the saved question names to add
DASHBOARD_MAP = {
    "Executive Dashboard": ["Total Revenue", "Daily Revenue", "Top Products", "Customer Geography"],
    "Customer Analytics": ["Total Customers", "Average Order Value", "Customer Geography", "Products by Category"],
    "Product Analytics": ["Products by Category", "Top Selling Products", "Top Products", "Total Revenue"],
}

session = requests.Session()

def api_login():
    r = session.post(f"{API}/session", json={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if r.status_code == 200:
        session.headers['X-Metabase-Session'] = r.json().get('id')
        return True
    print('API login failed', r.status_code, r.text)
    return False


def find_dashboard_by_name(name):
    # list dashboards via search endpoint
    r = session.get(f"{API}/dashboard")
    if r.status_code != 200:
        return None
    data = r.json()
    dashboards = data.get('data', data) if isinstance(data, dict) else data
    for d in dashboards:
        if d.get('name') == name:
            return d.get('id')
    return None


def find_card_by_name(name):
    r = session.get(f"{API}/card")
    if r.status_code != 200:
        return None
    data = r.json()
    cards = data.get('data', data) if isinstance(data, dict) else data
    for c in cards:
        if c.get('name') == name:
            return c.get('id')
    return None


def run_ui():
    if not api_login():
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(METABASE_URL)
        time.sleep(1)

        # Login via UI if needed
        if page.query_selector('input[name="username"]'):
            page.fill('input[name="username"]', ADMIN_EMAIL)
            page.fill('input[name="password"]', ADMIN_PASSWORD)
            page.click('button[type="submit"]')
            time.sleep(2)

        for dash_name, questions in DASHBOARD_MAP.items():
            dash_id = find_dashboard_by_name(dash_name)
            if not dash_id:
                print(f"Dashboard not found via API: {dash_name}; creating new dashboard")
                # create via API
                r = session.post(f"{API}/dashboard", json={"name": dash_name, "description": dash_name})
                if r.status_code == 200:
                    dash_id = r.json().get('id')
                else:
                    print('Failed to create dashboard via API', r.status_code, r.text)
                    continue

            # Open dashboard in edit mode
            page.goto(f"{METABASE_URL}/dashboard/{dash_id}?edit=true")
            time.sleep(2)

            for qname in questions:
                card_id = find_card_by_name(qname)
                if card_id:
                    # Click Add a question
                    try:
                        # Click the "Add" / "+" button
                        # The selector may vary; try a few common ones
                        if page.query_selector('button[aria-label="Add a question"]'):
                            page.click('button[aria-label="Add a question"]')
                        elif page.query_selector('button:has-text("Add a question")'):
                            page.click('button:has-text("Add a question")')
                        else:
                            # Try the top-right Add button
                            page.click('button[aria-label="Add"]')
                        time.sleep(0.8)

                        # In the modal, choose "Saved questions" tab
                        if page.query_selector('button:has-text("Saved questions")'):
                            page.click('button:has-text("Saved questions")')
                            time.sleep(0.5)

                        # Search for question by name
                        if page.query_selector('input[placeholder="Search questions and notebooks"]'):
                            page.fill('input[placeholder="Search questions and notebooks"]', qname)
                            time.sleep(0.6)

                        # Click the question result
                        # Try to click element that contains the exact name
                        page.click(f'text="{qname}"')
                        time.sleep(1.0)

                        # Click "Add to dashboard" button in modal
                        # The label might be "Add to dashboard" or "Add"
                        if page.query_selector('button:has-text("Add to dashboard")'):
                            page.click('button:has-text("Add to dashboard")')
                        elif page.query_selector('button:has-text("Add")'):
                            page.click('button:has-text("Add")')
                        time.sleep(1.0)
                        print(f"Added '{qname}' to {dash_name}")
                    except Exception as e:
                        print('UI add failed for', qname, e)
                else:
                    print(f"Card not found: {qname}")
            time.sleep(1.0)
        print('UI automation finished; dashboards should contain cards now')
        # Keep browser open for user to view
        print('Browser is open; press CTRL+C here to stop script while keeping browser open')
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            browser.close()

if __name__ == '__main__':
    run_ui()
