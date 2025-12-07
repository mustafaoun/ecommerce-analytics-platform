"""
Flask API for Ecommerce Analytics Platform
Serves reports, data, and dashboard endpoints
"""
import os
import json
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv

# Import project modules
from src.database.connection import get_engine
from src.visualization.report_generator import ReportGenerator
from src.etl.data_generator import (
    generate_users, generate_products, generate_orders,
    generate_order_items, generate_events
)
from src.etl.data_loader import DataLoader

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize engine and loader
engine = get_engine()
db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
loader = DataLoader(db_url)
report_gen = ReportGenerator(engine)

# ==================== HEALTH & STATUS ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503

@app.route('/api/status', methods=['GET'])
def status():
    """Platform status endpoint"""
    try:
        with engine.connect() as conn:
            # Count rows in each table
            tables = ['users', 'products', 'orders', 'order_items', 'events', 'marketing_campaigns']
            counts = {}
            for table in tables:
                result = conn.execute(f"SELECT COUNT(*) FROM {table}").scalar()
                counts[table] = result
        
        return jsonify({
            "status": "operational",
            "database": "connected",
            "tables": counts,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== DATA ENDPOINTS ====================

@app.route('/api/data/users', methods=['GET'])
def get_users():
    """Get users data with pagination"""
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    try:
        with engine.connect() as conn:
            query = f"""
                SELECT user_id, name, email, country, signup_date 
                FROM users 
                LIMIT {limit} OFFSET {offset}
            """
            result = conn.execute(query)
            rows = [dict(row) for row in result]
            
            # Get total count
            count = conn.execute("SELECT COUNT(*) FROM users").scalar()
            
        return jsonify({
            "data": rows,
            "total": count,
            "limit": limit,
            "offset": offset
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/data/orders', methods=['GET'])
def get_orders():
    """Get orders with user information"""
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    try:
        with engine.connect() as conn:
            query = f"""
                SELECT o.order_id, o.order_date, o.total_amount, o.status, u.name
                FROM orders o
                JOIN users u ON o.user_id = u.user_id
                ORDER BY o.order_date DESC
                LIMIT {limit} OFFSET {offset}
            """
            result = conn.execute(query)
            rows = [dict(row) for row in result]
            
            count = conn.execute("SELECT COUNT(*) FROM orders").scalar()
            
        return jsonify({
            "data": rows,
            "total": count,
            "limit": limit,
            "offset": offset
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== ANALYTICS ENDPOINTS ====================

@app.route('/api/analytics/revenue', methods=['GET'])
def get_revenue():
    """Get total revenue and trends"""
    try:
        with engine.connect() as conn:
            # Total revenue
            total = conn.execute(
                "SELECT SUM(total_amount)::numeric(12,2) FROM orders WHERE status='completed'"
            ).scalar()
            
            # Daily revenue (last 30 days)
            daily = conn.execute("""
                SELECT DATE(order_date) as date, SUM(total_amount)::numeric(12,2) as revenue
                FROM orders
                WHERE status='completed' AND order_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE(order_date)
                ORDER BY date DESC
            """)
            daily_data = [dict(row) for row in daily]
            
        return jsonify({
            "total_revenue": float(total) if total else 0,
            "currency": "USD",
            "daily_revenue": daily_data
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/top-products', methods=['GET'])
def get_top_products():
    """Get top products by revenue"""
    try:
        with engine.connect() as conn:
            query = """
                SELECT p.product_id, p.name, SUM(oi.quantity * oi.price_at_time)::numeric(12,2) as revenue
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                GROUP BY p.product_id, p.name
                ORDER BY revenue DESC
                LIMIT 10
            """
            result = conn.execute(query)
            rows = [dict(row) for row in result]
            
        return jsonify({"top_products": rows}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/customer-metrics', methods=['GET'])
def get_customer_metrics():
    """Get key customer metrics"""
    try:
        with engine.connect() as conn:
            metrics = {}
            
            # Total customers
            metrics['total_customers'] = conn.execute(
                "SELECT COUNT(DISTINCT user_id) FROM users"
            ).scalar()
            
            # Average order value
            metrics['avg_order_value'] = float(conn.execute(
                "SELECT AVG(total_amount)::numeric(12,2) FROM orders WHERE status='completed'"
            ).scalar() or 0)
            
            # Total orders
            metrics['total_orders'] = conn.execute(
                "SELECT COUNT(*) FROM orders WHERE status='completed'"
            ).scalar()
            
            # Repeat customer rate
            repeat = conn.execute("""
                SELECT COUNT(*) FROM users 
                WHERE user_id IN (SELECT user_id FROM orders GROUP BY user_id HAVING COUNT(*) > 1)
            """).scalar()
            metrics['repeat_customers'] = repeat
            metrics['repeat_rate'] = (repeat / metrics['total_customers'] * 100) if metrics['total_customers'] > 0 else 0
            
        return jsonify(metrics), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== ETL ENDPOINTS ====================

@app.route('/api/etl/generate-data', methods=['POST'])
def generate_data():
    """Generate new synthetic data"""
    try:
        n_users = request.json.get('n_users', 100) if request.json else 100
        n_products = request.json.get('n_products', 50) if request.json else 50
        
        users = generate_users(n=n_users)
        products = generate_products(n=n_products)
        orders, _ = generate_orders(n=200, users_df=users)
        order_items, orders = generate_order_items(orders, products)
        events = generate_events(n=645, users_df=users)
        
        return jsonify({
            "status": "success",
            "data_generated": {
                "users": len(users),
                "products": len(products),
                "orders": len(orders),
                "order_items": len(order_items),
                "events": len(events)
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/etl/load-data', methods=['POST'])
def load_data():
    """Load generated data to database"""
    try:
        from src.etl.data_generator import (
            generate_users, generate_products, generate_orders,
            generate_order_items, generate_events, generate_marketing_campaigns
        )
        
        # Generate data
        users = generate_users(n=100)
        products = generate_products(n=50)
        orders, _ = generate_orders(n=200, users_df=users)
        order_items, orders = generate_order_items(orders, products)
        events = generate_events(n=645, users_df=users)
        campaigns = generate_marketing_campaigns(n=10)
        
        # Load to database
        loader.load_data(users, 'users', truncate_first=True)
        loader.load_data(products, 'products', truncate_first=True)
        loader.load_data(orders, 'orders', truncate_first=True)
        loader.load_data(order_items, 'order_items', truncate_first=True)
        loader.load_data(events, 'events', truncate_first=True)
        loader.load_data(campaigns, 'marketing_campaigns', truncate_first=True)
        
        return jsonify({
            "status": "success",
            "message": "Data loaded successfully",
            "rows_loaded": {
                "users": len(users),
                "products": len(products),
                "orders": len(orders),
                "order_items": len(order_items),
                "events": len(events),
                "campaigns": len(campaigns)
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== DASHBOARD ENDPOINT ====================

@app.route('/', methods=['GET'])
def dashboard():
    """Render dashboard homepage"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ecommerce Analytics Platform</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; border-radius: 8px; margin-bottom: 30px; }
            h1 { font-size: 2.5em; margin-bottom: 10px; }
            .subtitle { font-size: 1.1em; opacity: 0.9; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .card h3 { margin-bottom: 15px; color: #333; }
            .card p { color: #666; line-height: 1.6; margin-bottom: 15px; }
            .btn { display: inline-block; background: #667eea; color: white; padding: 10px 20px; border-radius: 4px; text-decoration: none; cursor: pointer; border: none; font-size: 1em; }
            .btn:hover { background: #764ba2; }
            .links { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; }
            .metric { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }
            .metric-box { background: #f9f9f9; padding: 15px; border-left: 4px solid #667eea; }
            .metric-box .value { font-size: 2em; font-weight: bold; color: #667eea; }
            .metric-box .label { color: #666; font-size: 0.9em; margin-top: 5px; }
            code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📊 Ecommerce Analytics Platform</h1>
                <p class="subtitle">Real-time data warehouse with interactive dashboards</p>
            </header>
            
            <div class="grid">
                <div class="card">
                    <h3>🌐 Metabase Dashboard</h3>
                    <p>Interactive BI tool for data exploration and dashboarding.</p>
                    <a href="/metabase" class="btn">Open Dashboard →</a>
                </div>
                
                <div class="card">
                    <h3>📈 API Endpoints</h3>
                    <p>RESTful API for accessing analytics data and metrics.</p>
                    <div class="links">
                        <a href="/api/health" class="btn" style="background: #10b981;">Health</a>
                        <a href="/api/status" class="btn" style="background: #3b82f6;">Status</a>
                        <a href="/api/analytics/revenue" class="btn" style="background: #f59e0b;">Revenue</a>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🛠️ ETL Operations</h3>
                    <p>Generate and load synthetic data on demand.</p>
                    <div class="links">
                        <form action="/api/etl/load-data" method="POST" style="display:inline;">
                            <button type="submit" class="btn" style="background: #8b5cf6;">Load Data</button>
                        </form>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>📡 API Reference</h3>
                <table style="width:100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px;"><strong>Endpoint</strong></td>
                        <td style="padding: 10px;"><strong>Method</strong></td>
                        <td style="padding: 10px;"><strong>Description</strong></td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px;"><code>/api/health</code></td>
                        <td style="padding: 10px;">GET</td>
                        <td style="padding: 10px;">Health check</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px;"><code>/api/status</code></td>
                        <td style="padding: 10px;">GET</td>
                        <td style="padding: 10px;">Platform status and table counts</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px;"><code>/api/data/users</code></td>
                        <td style="padding: 10px;">GET</td>
                        <td style="padding: 10px;">Get users data with pagination</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px;"><code>/api/data/orders</code></td>
                        <td style="padding: 10px;">GET</td>
                        <td style="padding: 10px;">Get orders with user info</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px;"><code>/api/analytics/revenue</code></td>
                        <td style="padding: 10px;">GET</td>
                        <td style="padding: 10px;">Total and daily revenue</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px;"><code>/api/analytics/top-products</code></td>
                        <td style="padding: 10px;">GET</td>
                        <td style="padding: 10px;">Top 10 products by revenue</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px;"><code>/api/analytics/customer-metrics</code></td>
                        <td style="padding: 10px;">GET</td>
                        <td style="padding: 10px;">Customer KPIs</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px;"><code>/api/etl/generate-data</code></td>
                        <td style="padding: 10px;">POST</td>
                        <td style="padding: 10px;">Generate synthetic data</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px;"><code>/api/etl/load-data</code></td>
                        <td style="padding: 10px;">POST</td>
                        <td style="padding: 10px;">Load data to database</td>
                    </tr>
                </table>
            </div>
            
            <div class="card" style="margin-top: 20px; background: #f0f9ff;">
                <h3>🚀 Quick Start</h3>
                <p><strong>1. Check Platform Status:</strong></p>
                <code style="display: block; padding: 10px; background: white; margin: 10px 0;">curl https://your-app.herokuapp.com/api/status</code>
                
                <p style="margin-top: 15px;"><strong>2. Load Sample Data:</strong></p>
                <code style="display: block; padding: 10px; background: white; margin: 10px 0;">curl -X POST https://your-app.herokuapp.com/api/etl/load-data</code>
                
                <p style="margin-top: 15px;"><strong>3. View Analytics:</strong></p>
                <code style="display: block; padding: 10px; background: white; margin: 10px 0;">curl https://your-app.herokuapp.com/api/analytics/revenue</code>
                
                <p style="margin-top: 15px;"><strong>4. Access Metabase:</strong></p>
                <code style="display: block; padding: 10px; background: white; margin: 10px 0;">Visit https://your-app.herokuapp.com/metabase</code>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/metabase')
def metabase_redirect():
    """Redirect to Metabase"""
    return f"""
    <html>
    <head>
        <title>Redirecting to Metabase...</title>
        <meta http-equiv="refresh" content="0; url=http://metabase:3000" />
    </head>
    <body>
        <p>Redirecting to Metabase...</p>
    </body>
    </html>
    """

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
