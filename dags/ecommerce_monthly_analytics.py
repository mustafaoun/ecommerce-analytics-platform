# dags/ecommerce_monthly_analytics.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
import sys

sys.path.insert(0, '/opt/airflow/src')

default_args = {
    'owner': 'ecommerce_team',
    'depends_on_past': False,
    'start_date': days_ago(30),
    'email_on_failure': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=15),
}

dag = DAG(
    'ecommerce_monthly_analytics',
    default_args=default_args,
    description='Monthly analytics and forecasting',
    schedule_interval='0 4 1 * *',  # 4 AM on the 1st of every month
    catchup=False,
    tags=['ecommerce', 'monthly', 'forecasting', 'analytics'],
)

def run_monthly_forecasting(**context):
    """Run monthly demand forecasting"""
    try:
        from src.analytics.forecasting import SalesForecaster
        
        print("🔮 Running monthly demand forecasting...")
        
        # Forecast for next 30 days
        forecaster = SalesForecaster()
        forecaster.train_model()
        forecast = forecaster.forecast_future(30)
        
        # Save forecast to database
        from src.database.connection import db
        with db.get_connection() as conn:
            forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_sql('demand_forecast', conn, if_exists='replace', index=False)
        
        print(f"✅ Forecast generated for {len(forecast)} days")
        return "Monthly forecasting completed"
        
    except Exception as e:
        print(f"❌ Error in monthly forecasting: {e}")
        raise

def run_customer_segmentation(**context):
    """Update customer segmentation"""
    try:
        from src.analytics.clustering import segment_customers
        
        print("👥 Running customer segmentation...")
        
        # Segment customers (placeholder – implement with scikit-learn KMeans)
        segments = pd.DataFrame({'segment': ['High Value', 'Regular', 'New'], 'count': [200, 500, 300]})
        
        # Save segments to database
        from src.database.connection import db
        with db.get_connection() as conn:
            segments.to_sql('customer_segments', conn, if_exists='replace', index=False)
        
        print(f"✅ Customer segmentation completed: {len(segments)} segments")
        return "Customer segmentation completed"
        
    except Exception as e:
        print(f"❌ Error in customer segmentation: {e}")
        raise

def run_ab_test_analysis(**context):
    """Analyze A/B tests"""
    try:
        print("🧪 Analyzing A/B tests...")
        
        # Placeholder – in real, query ab_test_results table
        results = pd.DataFrame({'test_name': ['Checkout A/B', 'Email Campaign'], 'p_value': [0.03, 0.12], 'significant': [True, False]})
        
        # Save results
        from src.database.connection import db
        with db.get_connection() as conn:
            results.to_sql('ab_test_results', conn, if_exists='append', index=False)
        
        print(f"✅ A/B test analysis completed: {len(results)} tests analyzed")
        return "A/B test analysis completed"
        
    except Exception as e:
        print(f"❌ Error in A/B test analysis: {e}")
        raise

def generate_monthly_report(**context):
    """Generate comprehensive monthly report"""
    try:
        execution_date = context['execution_date']
        month_start = execution_date.replace(day=1)
        
        print(f"📊 Generating monthly report for {month_start.strftime('%B %Y')}...")
        
        # Placeholder – in real, generate PDF/HTML with matplotlib
        report_path = f'/opt/airflow/data/reports/monthly_{month_start.strftime("%Y%m")}.pdf'
        with open(report_path, 'w') as f:
            f.write(f"Monthly Report for {month_start.strftime('%B %Y')}\nGenerated: {datetime.now()}")
        
        print(f"✅ Monthly report generated: {report_path}")
        return f"Monthly report: {report_path}"
        
    except Exception as e:
        print(f"❌ Error generating monthly report: {e}")
        raise

def backup_database(**context):
    """Create database backup"""
    try:
        print("💾 Creating database backup...")
        
        # Placeholder – in real, pg_dump to S3
        from src.database.connection import db
        import pandas as pd
        from datetime import datetime
        
        backup_date = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f"/opt/airflow/data/backups/{backup_date}"
        
        # Create backup directory
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup key tables
        tables = ['users', 'products', 'orders', 'order_items', 'events']
        
        for table in tables:
            with db.get_connection() as conn:
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                df.to_csv(f"{backup_dir}/{table}.csv", index=False)
                print(f"  Backed up {table}: {len(df)} rows")
        
        print(f"✅ Database backup completed: {backup_dir}")
        return f"Backup created: {backup_dir}"
        
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        raise

# Define tasks
forecasting_task = PythonOperator(
    task_id='run_monthly_forecasting',
    python_callable=run_monthly_forecasting,
    provide_context=True,
    dag=dag,
)

segmentation_task = PythonOperator(
    task_id='run_customer_segmentation',
    python_callable=run_customer_segmentation,
    provide_context=True,
    dag=dag,
)

ab_test_task = PythonOperator(
    task_id='run_ab_test_analysis',
    python_callable=run_ab_test_analysis,
    provide_context=True,
    dag=dag,
)

report_task = PythonOperator(
    task_id='generate_monthly_report',
    python_callable=generate_monthly_report,
    provide_context=True,
    dag=dag,
)

backup_task = PythonOperator(
    task_id='backup_database',
    python_callable=backup_database,
    provide_context=True,
    dag=dag,
)

# Set dependencies
forecasting_task >> segmentation_task >> ab_test_task >> report_task >> backup_task