# dags/ecommerce_weekly_aggregations.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.postgres_operator import PostgresOperator
from airflow.utils.dates import days_ago
import sys
import os

sys.path.insert(0, '/opt/airflow/src')

default_args = {
    'owner': 'ecommerce_team',
    'depends_on_past': False,
    'start_date': days_ago(7),
    'email_on_failure': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
}

dag = DAG(
    'ecommerce_weekly_aggregations',
    default_args=default_args,
    description='Weekly aggregations and reporting',
    schedule_interval='0 3 * * 1',  # Every Monday at 3 AM
    catchup=False,
    tags=['ecommerce', 'weekly', 'aggregations'],
)

def calculate_weekly_kpis(**context):
    """Calculate weekly KPIs"""
    try:
        from src.database.connection import db
        
        execution_date = context['execution_date']
        week_start = execution_date - timedelta(days=7)
        
        print(f"📊 Calculating weekly KPIs for week starting {week_start.date()}...")
        
        query = """
        INSERT INTO weekly_kpis (week_start, active_users, total_orders, total_revenue, avg_order_value, new_customers)
        SELECT 
            DATE_TRUNC('week', order_date) as week_start,
            COUNT(DISTINCT user_id) as active_users,
            COUNT(DISTINCT order_id) as total_orders,
            SUM(total_amount) as total_revenue,
            AVG(total_amount) as avg_order_value,
            COUNT(DISTINCT CASE WHEN u.signup_date >= DATE_TRUNC('week', order_date) 
                AND u.signup_date < DATE_TRUNC('week', order_date) + INTERVAL '7 days' 
                THEN u.user_id END) as new_customers
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        WHERE order_date >= %s AND order_date < %s
        GROUP BY DATE_TRUNC('week', order_date)
        ON CONFLICT (week_start) DO UPDATE SET
            active_users = EXCLUDED.active_users,
            total_orders = EXCLUDED.total_orders,
            total_revenue = EXCLUDED.total_revenue,
            avg_order_value = EXCLUDED.avg_order_value,
            new_customers = EXCLUDED.new_customers,
            updated_at = CURRENT_TIMESTAMP;
        """
        
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (week_start, week_start + timedelta(days=7)))
                conn.commit()
        
        print("✅ Weekly KPIs calculated")
        return "Weekly KPIs calculated"
        
    except Exception as e:
        print(f"❌ Error calculating weekly KPIs: {e}")
        raise

def generate_weekly_report(**context):
    """Generate weekly report"""
    try:
        from src.analytics.weekly_report import generate_report
        
        execution_date = context['execution_date']
        week_start = execution_date - timedelta(days=7)
        
        print(f"📄 Generating weekly report for week starting {week_start.date()}...")
        
        # Generate and save report
        report_path = generate_report(week_start)
        
        print(f"✅ Weekly report generated: {report_path}")
        return f"Weekly report generated: {report_path}"
        
    except Exception as e:
        print(f"❌ Error generating weekly report: {e}")
        raise

def cleanup_old_data(**context):
    """Cleanup old data (keep 90 days)"""
    try:
        from src.database.connection import db
        
        print("🧹 Cleaning up old data...")
        
        cutoff_date = datetime.now() - timedelta(days=90)
        
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Archive old events (in production, you might archive instead of delete)
                cur.execute("""
                DELETE FROM events 
                WHERE timestamp < %s 
                """, (cutoff_date,))
                
                events_deleted = cur.rowcount
                
                # Update statistics
                cur.execute("ANALYZE events;")
                
                conn.commit()
        
        print(f"✅ Cleaned up {events_deleted} old event records")
        return f"Cleaned up {events_deleted} records"
        
    except Exception as e:
        print(f"❌ Error cleaning up data: {e}")
        raise

# Create weekly KPIs table if not exists
create_weekly_table = PostgresOperator(
    task_id='create_weekly_kpis_table',
    postgres_conn_id='postgres_default',
    sql="""
    CREATE TABLE IF NOT EXISTS weekly_kpis (
        week_start DATE PRIMARY KEY,
        active_users INTEGER,
        total_orders INTEGER,
        total_revenue DECIMAL(10,2),
        avg_order_value DECIMAL(10,2),
        new_customers INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    dag=dag,
)

calculate_weekly_kpis_task = PythonOperator(
    task_id='calculate_weekly_kpis',
    python_callable=calculate_weekly_kpis,
    provide_context=True,
    dag=dag,
)

generate_report_task = PythonOperator(
    task_id='generate_weekly_report',
    python_callable=generate_weekly_report,
    provide_context=True,
    dag=dag,
)

cleanup_task = PythonOperator(
    task_id='cleanup_old_data',
    python_callable=cleanup_old_data,
    provide_context=True,
    dag=dag,
)

# Set dependencies
create_weekly_table >> calculate_weekly_kpis_task >> generate_report_task >> cleanup_task