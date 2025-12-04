from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.dates import days_ago
import sys
import os

# Add src to Python path
sys.path.insert(0, '/opt/airflow/src')

default_args = {
    'owner': 'ecommerce_team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email': ['your-email@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}

dag = DAG(
    'ecommerce_daily_pipeline',
    default_args=default_args,
    description='Daily ETL pipeline for e-commerce analytics',
    schedule_interval='0 2 * * *',  # Run at 2 AM every day
    catchup=False,
    tags=['ecommerce', 'etl', 'analytics'],
    max_active_runs=1,
)

def run_etl():
    """Run the ETL pipeline"""
    try:
        os.chdir('/opt/airflow')
        # Use absolute path for scripts
        result = os.system('python /opt/airflow/scripts/run_etl.py')
        if result == 0:
            print("✅ ETL pipeline completed successfully")
            return "ETL success"
        else:
            print("ETL pipeline failed with code: " + str(result))
            return "ETL failed"
    except Exception as e:
        print(f"❌ ETL error: {e}")
        return "ETL error"

start_task = EmptyOperator(
    task_id='start_pipeline',
    dag=dag,
)

etl_task = PythonOperator(
    task_id='run_etl',
    python_callable=run_etl,
    dag=dag,
)

end_task = EmptyOperator(
    task_id='end_pipeline',
    dag=dag,
)

start_task >> etl_task >> end_task