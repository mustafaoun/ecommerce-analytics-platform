import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db 
import pandas as pd
from tabulate import tabulate

def run_verification_queries():
    """Run verification queries to ensure data quality"""
    
    print("🔍 Verifying E-commerce Data Quality")
    print("=" * 60)
    
    queries = [
        ("📊 User Statistics", """
        SELECT 
            COUNT(*) as total_users,
            COUNT(DISTINCT country) as countries_represented,
            -- FINAL FIX: Direct date subtraction returns days (an integer), which can be averaged. 
            -- DATE_PART is not needed for DATE - DATE difference in PostgreSQL.
            ROUND(AVG(CURRENT_DATE - signup_date), 1) as avg_account_age_days, 
            MIN(signup_date) as earliest_signup,
            MAX(signup_date) as latest_signup
        FROM users;
        """),
        
        ("💰 Product Statistics", """
        SELECT 
            COUNT(*) as total_products,
            COUNT(DISTINCT category) as categories,
            ROUND(AVG(price), 2) as avg_price,
            ROUND(MIN(price), 2) as min_price,
            ROUND(MAX(price), 2) as max_price
        FROM products;
        """),
        
        ("🛒 Order Statistics", """
        SELECT 
            COUNT(*) as total_orders,
            ROUND(SUM(total_amount), 2) as total_revenue,
            ROUND(AVG(total_amount), 2) as avg_order_value,
            MIN(order_date) as first_order,
            MAX(order_date) as last_order
        FROM orders;
        """),
        
        ("📈 Daily Revenue (Last 7 Days)", """
        SELECT 
            DATE(order_date) as order_day,
            COUNT(*) as orders,
            ROUND(SUM(total_amount), 2) as daily_revenue,
            ROUND(AVG(total_amount), 2) as avg_order_value
        FROM orders
        WHERE order_date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY DATE(order_date)
        ORDER BY order_day DESC;
        """),
        
        ("🏆 Top 5 Products by Revenue", """
        SELECT 
            p.name,
            p.category,
            COUNT(oi.order_item_id) as units_sold,
            ROUND(SUM(oi.quantity * oi.price_at_time), 2) as total_revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        GROUP BY p.product_id, p.name, p.category
        ORDER BY total_revenue DESC
        LIMIT 5;
        """),
        
        ("🌍 User Geography", """
        SELECT 
            country,
            COUNT(*) as user_count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
        FROM users
        GROUP BY country
        ORDER BY user_count DESC;
        """),
        
        ("📱 Acquisition Channels", """
        SELECT 
            acquisition_channel,
            COUNT(*) as users,
            COUNT(DISTINCT o.order_id) as orders,
            ROUND(SUM(o.total_amount), 2) as revenue
        FROM users u
        LEFT JOIN orders o ON u.user_id = o.user_id
        GROUP BY acquisition_channel
        ORDER BY revenue DESC NULLS LAST;
        """)
    ]
    
    with db.get_connection() as conn:
        for title, query in queries:
            print(f"\n{title}")
            print("-" * len(title))
            
            try:
                df = pd.read_sql_query(query, conn)
                print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            except Exception as e:
                print(f"❌ Query failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Verification Complete!")
    
    # Data quality checks
    print("\n🔬 Data Quality Checks:")
    
    quality_queries = [
        ("Check for NULL emails in users", "SELECT COUNT(*) FROM users WHERE email IS NULL", 0),
        ("Check for negative prices", "SELECT COUNT(*) FROM products WHERE price < 0", 0),
        ("Check for future orders", "SELECT COUNT(*) FROM orders WHERE order_date > NOW()", 0),
        ("Check order consistency (orders without items)", """
        SELECT COUNT(*) FROM orders o
        WHERE NOT EXISTS (
            SELECT 1 FROM order_items oi 
            WHERE oi.order_id = o.order_id
        )
        """, 0)
    ]
    
    with db.get_connection() as conn:
        for check_name, query, expected in quality_queries:
            result = pd.read_sql_query(query, conn)
            count = result.iloc[0, 0]
            status = "✅ PASS" if count == expected else f"❌ FAIL ({count} found)"
            print(f"  {check_name}: {status}")

def generate_sample_queries_file():
    """Generate a file with sample queries for analysis"""
    
    sample_queries = """
-- Sample SQL Queries for E-commerce Analysis
-- ===========================================

-- 1. Monthly Revenue Trend
SELECT 
    DATE_TRUNC('month', order_date) as month,
    COUNT(DISTINCT order_id) as orders,
    ROUND(SUM(total_amount), 2) as revenue,
    ROUND(AVG(total_amount), 2) as avg_order_value
FROM orders
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month DESC;

-- 2. Customer Retention (Cohort Analysis)
WITH user_cohorts AS (
    SELECT 
        user_id,
        DATE_TRUNC('month', signup_date) as cohort_month
    FROM users
),
monthly_orders AS (
    SELECT 
        u.user_id,
        u.cohort_month,
        DATE_TRUNC('month', o.order_date) as order_month,
        COUNT(DISTINCT o.order_id) as orders
    FROM user_cohorts u
    LEFT JOIN orders o ON u.user_id = o.user_id
    GROUP BY 1, 2, 3
)
SELECT 
    cohort_month,
    order_month,
    COUNT(DISTINCT user_id) as active_users
FROM monthly_orders
GROUP BY cohort_month, order_month
ORDER BY cohort_month, order_month;

-- 3. Product Category Performance
SELECT 
    p.category,
    COUNT(DISTINCT oi.order_id) as orders,
    SUM(oi.quantity) as units_sold,
    ROUND(SUM(oi.quantity * oi.price_at_time), 2) as revenue,
    ROUND(SUM(oi.quantity * (oi.price_at_time - p.cost)), 2) as profit
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.category
ORDER BY revenue DESC;

-- 4. Customer Lifetime Value
SELECT 
    u.user_id,
    u.email,
    u.signup_date,
    COUNT(DISTINCT o.order_id) as total_orders,
    ROUND(SUM(o.total_amount), 2) as total_spent,
    ROUND(AVG(o.total_amount), 2) as avg_order_value,
    MIN(o.order_date) as first_order,
    MAX(o.order_date) as last_order
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.email, u.signup_date
ORDER BY total_spent DESC NULLS LAST;

-- 5. Hourly Sales Distribution
SELECT 
    EXTRACT(HOUR FROM order_date) as hour_of_day,
    COUNT(*) as orders,
    ROUND(SUM(total_amount), 2) as revenue
FROM orders
GROUP BY EXTRACT(HOUR FROM order_date)
ORDER BY hour_of_day;
"""
    
    with open('sample_queries.sql', 'w') as f:
        f.write(sample_queries)
    
    print("\n📄 Sample queries saved to 'sample_queries.sql'")

if __name__ == "__main__":
    run_verification_queries()
    generate_sample_queries_file()
    
    print("\n🎯 Next Steps:")
    print("1. Run: python sample_queries.sql in your SQL client")
    print("2. Start building Power BI dashboard")
    print("3. Set up Airflow for automation")