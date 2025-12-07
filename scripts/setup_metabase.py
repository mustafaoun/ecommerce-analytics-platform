# scripts/setup_metabase.py
import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

class MetabaseSetup:
    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
        self.session = None
        self.headers = {"Content-Type": "application/json"}
    
    def wait_for_metabase(self, max_retries=30):
        """Wait for Metabase to be ready"""
        print("⏳ Waiting for Metabase to start...")
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/api/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Metabase is ready!")
                    return True
            except:
                pass
            
            print(f"  Attempt {i+1}/{max_retries}...")
            time.sleep(2)
        
        print("❌ Metabase failed to start")
        return False
    
    def setup_admin(self, email="admin@ecommerce.com", password="EcommerceAdmin2025!"):
        """Setup admin user (skip if already exists)"""
        print("👤 Setting up admin user...")
        
        setup_url = f"{self.base_url}/api/setup"
        
        # Get setup token
        token = self._get_setup_token()
        
        setup_data = {
            "token": token,
            "user": {
                "first_name": "Admin",
                "last_name": "User",
                "email": email,
                "password": password
            },
            "prefs": {
                "site_name": "E-commerce Analytics",
                "site_locale": "en"
            },
            "database": None,  # We'll add database later
            "invite": None
        }
        
        response = requests.post(setup_url, json=setup_data, headers=self.headers)
        
        if response.status_code == 200:
            print("✅ Admin user created")
            self.session_token = response.json()["id"]
            self.headers["X-Metabase-Session"] = self.session_token
            return True
        elif "user currently exists" in response.text.lower():
            print("⚠️ Admin user already exists – skipping creation")
            # Try to login to get session
            login_data = {
                "username": email,
                "password": password
            }
            login_response = requests.post(f"{self.base_url}/api/session", json=login_data, headers=self.headers)
            if login_response.status_code == 200:
                self.session_token = login_response.json()["id"]
                self.headers["X-Metabase-Session"] = self.session_token
                print("✅ Logged in to existing admin")
                return True
            else:
                print("❌ Failed to login to existing admin – manual login required")
                return False
        else:
            print(f"❌ Failed to create admin: {response.text}")
            return False
    
    def _get_setup_token(self):
        """Get setup token from Metabase"""
        response = requests.get(f"{self.base_url}/api/session/properties")
        if response.status_code == 200:
            # Check if setup-token exists. If not, setup is likely complete.
            return response.json().get("setup-token")
        return None
    
    def add_postgres_database(self):
        """Add PostgreSQL database connection"""
        print("🗄️ Adding PostgreSQL database connection...")
        
        db_url = f"{self.base_url}/api/database"
        
        db_config = {
            "name": "E-commerce Database",
            "engine": "postgres",
            "details": {
                "host": os.getenv("DB_HOST"),
                "port": int(os.getenv("DB_PORT", 5432)),
                "dbname": os.getenv("DB_NAME"),
                "user": os.getenv("DB_USER"),
                "password": os.getenv("DB_PASSWORD"),
                "ssl": False,
                "additional-options": None,
                "tunnel-enabled": False
            },
            "is_full_sync": True,
            "is_on_demand": False,
            "auto_run_queries": True
        }
        
        response = requests.post(db_url, json=db_config, headers=self.headers)
        
        if response.status_code == 200:
            print("✅ Database connection added")
            return response.json()["id"]
        else:
            print(f"❌ Failed to add database: {response.text}")
            return None
    
    def create_collection(self, name, description="", color="#509EE3", parent_id=None):
        """Create a collection for organizing dashboards"""
        print(f"📁 Creating collection: {name}...")
        
        collection_url = f"{self.base_url}/api/collection"
        collection_data = {
            "name": name,
            "description": description,
            "color": color,
            "parent_id": parent_id
        }
        
        response = requests.post(collection_url, json=collection_data, headers=self.headers)
        
        if response.status_code == 200:
            collection_id = response.json()["id"]
            print(f"✅ Collection created (ID: {collection_id})")
            return collection_id
        else:
            print(f"❌ Failed to create collection: {response.text}")
            return None
    
    def create_dashboard(self, name, description="", collection_id=None):
        """Create a new dashboard"""
        print(f"📊 Creating dashboard: {name}...")
        
        dashboard_url = f"{self.base_url}/api/dashboard"
        dashboard_data = {
            "name": name,
            "description": description,
            "collection_id": collection_id,
            "parameters": [],
            "cache_ttl": None
        }
        
        response = requests.post(dashboard_url, json=dashboard_data, headers=self.headers)
        
        if response.status_code == 200:
            dashboard_id = response.json()["id"]
            print(f"✅ Dashboard created (ID: {dashboard_id})")
            return dashboard_id
        else:
            print(f"❌ Failed to create dashboard: {response.text}")
            return None
    
    def create_question(self, name, query, visualization_settings=None, collection_id=None):
        """Create a saved question (chart)"""
        print(f"📈 Creating question: {name}...")
        
        question_url = f"{self.base_url}/api/card"
        question_data = {
            "name": name,
            "dataset_query": {
                "database": 1,  # Default database ID (assuming it's 1 for the first one added)
                "type": "native",
                "native": {
                    "query": query
                }
            },
            "display": "table",
            "visualization_settings": visualization_settings or {},
            "collection_id": collection_id,
            "result_metadata": []
        }
        
        response = requests.post(question_url, json=question_data, headers=self.headers)
        
        if response.status_code == 200:
            question_id = response.json()["id"]
            print(f"✅ Question created (ID: {question_id})")
            return question_id
        else:
            print(f"❌ Failed to create question: {response.text}")
            return None
    
    def add_card_to_dashboard(self, dashboard_id, card_id, row=0, col=0, size_x=4, size_y=3):
        """
        Add a card to the dashboard. 
        FIX: Uses GET + PUT on the main dashboard endpoint (/api/dashboard/{id}) 
        to ensure compatibility with modern Metabase versions.
        """
        print(f"➕ Adding card {card_id} to dashboard {dashboard_id}...")
        
        dashboard_url = f"{self.base_url}/api/dashboard/{dashboard_id}"
        
        # 1. GET the current dashboard definition
        get_response = requests.get(dashboard_url, headers=self.headers)
        if get_response.status_code != 200:
            print(f"❌ Failed to retrieve dashboard {dashboard_id}: {get_response.status_code}")
            return False
            
        dashboard_data = get_response.json()
        
        # 2. Append the new dashcard definition
        new_dashcard = {
            # 'id' is often set to None for a new dashcard being added to the list
            "id": None, 
            "cardId": card_id,
            "row": row,
            "col": col,
            "sizeX": size_x,
            "sizeY": size_y,
            # Including necessary default fields
            "series": [],
            "visualization_settings": {},
            "parameter_mappings": [],
            "dashboard_id": dashboard_id 
        }
        
        # Ensure 'ordered_cards' exists and append the new card
        if 'ordered_cards' not in dashboard_data:
             dashboard_data['ordered_cards'] = []

        dashboard_data['ordered_cards'].append(new_dashcard)
        
        # 3. PUT the full, updated dashboard definition back
        put_response = requests.put(dashboard_url, json=dashboard_data, headers=self.headers)
        
        if put_response.status_code == 200:
            print("✅ Card added to dashboard")
            return True
        else:
            print(f"⚠️ Failed to add card {card_id}: {put_response.status_code} - {put_response.text}")
            print("   Manual addition recommended in UI")
            return False
    
    def setup_sample_dashboard(self):
        """Setup a sample dashboard with key metrics"""
        
        # Create collections
        main_collection = self.create_collection(
            "E-commerce Analytics",
            "Main dashboards and reports",
            "#509EE3"
        )
        
        # Create dashboard
        dashboard_id = self.create_dashboard(
            "Executive Dashboard",
            "Overview of key e-commerce metrics",
            main_collection
        )
        
        # Create sample questions
        queries = [
            {
                "name": "Daily Revenue Trend",
                "query": """
                SELECT 
                    DATE(order_date) as date,
                    SUM(total_amount) as revenue,
                    COUNT(*) as orders
                FROM orders 
                WHERE status = 'completed'
                GROUP BY DATE(order_date)
                ORDER BY date DESC
                LIMIT 30
                """,
                "viz": {"display": "line"}
            },
            {
                "name": "Top Products by Revenue",
                "query": """
                SELECT 
                    p.name,
                    p.category,
                    SUM(oi.quantity * oi.price_at_time) as revenue,
                    SUM(oi.quantity) as units_sold
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                JOIN orders o ON oi.order_id = o.order_id
                WHERE o.status = 'completed'
                GROUP BY p.product_id, p.name, p.category
                ORDER BY revenue DESC
                LIMIT 10
                """,
                "viz": {"display": "bar"}
            },
            {
                "name": "Customer Geography",
                "query": """
                SELECT 
                    u.country,
                    COUNT(DISTINCT u.user_id) as customers,
                    SUM(o.total_amount) as revenue
                FROM users u
                LEFT JOIN orders o ON u.user_id = o.user_id
                WHERE o.status = 'completed' OR o.order_id IS NULL
                GROUP BY u.country
                ORDER BY revenue DESC NULLS LAST
                """,
                "viz": {"display": "table"}
            }
        ]
        
        # Add cards to dashboard in a grid
        for i, query_info in enumerate(queries):
            card_id = self.create_question(
                query_info["name"],
                query_info["query"],
                query_info["viz"],
                main_collection
            )
            
            if card_id and dashboard_id:
                # Arrange in 3-column grid
                row = (i // 3) * 4
                col = (i % 3) * 4
                self.add_card_to_dashboard(dashboard_id, card_id, row, col)
        
        print("✅ Sample dashboard created!")
        return dashboard_id
    
    def run_full_setup(self):
        """Run complete Metabase setup"""
        print("🚀 Starting Metabase setup...")
        
        if not self.wait_for_metabase():
            return False
        
        if not self.setup_admin():
            return False
        
        db_id = self.add_postgres_database()
        if not db_id:
            return False
        
        # Wait for sync
        print("⏳ Waiting for database sync...")
        time.sleep(10)
        
        self.setup_sample_dashboard()
        
        print("\n" + "="*50)
        print("🎉 METABASE SETUP COMPLETE!")
        print("="*50)
        print(f"\n📊 Access Metabase: {self.base_url}")
        print("   Email: admin@ecommerce.com")
        print("   Password: EcommerceAdmin2025!")
        print("\n📋 Next steps:")
        print("   1. Log in and explore the sample dashboard")
        print("   2. Create more questions and dashboards")
        print("   3. Set up email subscriptions")
        print("   4. Configure user permissions")

def main():
    """Main setup function"""
    print("="*60)
    print("🔧 METABASE SETUP FOR E-COMMERCE ANALYTICS")
    print("="*60)
    
    # Check if Metabase is running
    try:
        setup = MetabaseSetup()
        setup.run_full_setup()
    except Exception as e:
        print(f"❌ Setup error: {e}")
        print("\n💡 Make sure Metabase is running:")
        print("   docker-compose -f docker-compose.metabase.yml up -d")

if __name__ == "__main__":
    main()