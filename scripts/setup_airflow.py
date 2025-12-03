# scripts/setup_airflow.py
import os
import sys
from pathlib import Path

def setup_airflow_environment():
    """Setup Airflow environment and create necessary directories"""
    
    print("🔧 Setting up Airflow environment...")
    
    # Create required directories
    directories = ['dags', 'logs', 'plugins', 'data/airflow']
    
    for dir_name in directories:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
        print(f"  Created: {dir_name}/")
    
    # Create .env file for Airflow if it doesn't exist
    if not os.path.exists('.env.airflow'):
        with open('.env.airflow', 'w') as f:
            f.write("""# Airflow Environment Variables
AIRFLOW_UID=50000
AIRFLOW_GID=50000

# Database Connection (for your ecommerce DB)
DB_HOST=aws-1-eu-west-1.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres.uquruuixtmkpgivbtcjx
DB_PASSWORD=5tF?36UXz$gFzb6
""")
        print("  Created: .env.airflow (updated with your Supabase creds)")
    
    # Create requirements-airflow.txt
    if not os.path.exists('requirements-airflow.txt'):
        with open('requirements-airflow.txt', 'w') as f:
            f.write("""# Airflow requirements
apache-airflow==2.6.3
apache-airflow-providers-postgres==5.0.0
apache-airflow-providers-http==4.5.0
apache-airflow-providers-cncf-kubernetes==5.1.0

# Ecommerce project requirements
pandas>=2.0.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
faker>=18.0.0
prophet>=1.1.0
scikit-learn>=1.3.0
""")
        print("  Created: requirements-airflow.txt")
    
    print("\n✅ Airflow environment setup complete!")
    print("\nNext steps:")
    print("1. Run: docker-compose -f docker-compose.airflow.yml up -d")
    print("2. Access Airflow at: http://localhost:8080")
    print("   Username: admin")
    print("   Password: admin")

if __name__ == "__main__":
    setup_airflow_environment()