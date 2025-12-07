#!/usr/bin/env python
# scripts/deploy_platform.py
import os
import sys
import subprocess
import time
from pathlib import Path
import webbrowser
from datetime import datetime

class EcommercePlatformDeployer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.services = {
            'database': False,
            'airflow': False,
            'metabase': False,
            'reports': False
        }

    def check_prerequisites(self):
        """Check if all prerequisites are installed"""
        print("🔍 Checking prerequisites...")

        prerequisites = {
            'Docker': ['docker', '--version'],
            'Docker Compose': ['docker-compose', '--version'],
            'Python': ['python', '--version'],
            'Git': ['git', '--version']
        }

        all_ok = True
        for name, cmd in prerequisites.items():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"  ✅ {name}: {result.stdout.strip()}")
                else:
                    print(f"  ❌ {name}: Not found")
                    all_ok = False
            except FileNotFoundError:
                print(f"  ❌ {name}: Not installed")
                all_ok = False

        return all_ok

    def setup_environment(self):
        """Setup Python environment"""
        print("\n🐍 Setting up Python environment...")

        # Check if virtual environment exists
        venv_path = self.project_root / 'venv'
        if not venv_path.exists():
            print("  Creating virtual environment...")
            subprocess.run(['python', '-m', 'venv', 'venv'], cwd=self.project_root)

        # Install requirements
        requirements_file = self.project_root / 'requirements.txt'
        if requirements_file.exists():
            print("  Installing Python packages...")

            # Determine pip path based on OS
            pip_path = 'venv\\Scripts\\pip' if os.name == 'nt' else 'venv/bin/pip'

            subprocess.run([pip_path, 'install', '-r', 'requirements.txt'],
                          cwd=self.project_root, check=True)

        print("  ✅ Environment setup complete")

    def setup_database(self):
        """Setup and populate database"""
        print("\n🗄️ Setting up database...")

        try:
            # Run schema creation
            print("  Creating database schema...")
            subprocess.run(['python', 'scripts/create_schema.py'],
                          cwd=self.project_root, check=True)

            # Run ETL pipeline
            print("  Loading initial data...")
            subprocess.run(['python', 'scripts/run_etl.py'],
                          cwd=self.project_root, check=True)

            # Create Power BI views
            print("  Creating Power BI views...")
            db_script = self.project_root / 'src' / 'database' / 'powerbi_views.sql'
            if db_script.exists():
                from src.database.connection import db
                with open(db_script, 'r') as f:
                    sql_commands = f.read()

                with db.get_connection() as conn:
                    conn.autocommit = True
                    with conn.cursor() as cur:
                        for command in sql_commands.split(';'):
                            command = command.strip()
                            if command:
                                try:
                                    cur.execute(command)
                                except Exception as e:
                                    print(f"    Warning: {e}")

            self.services['database'] = True
            print("  ✅ Database setup complete")

        except subprocess.CalledProcessError as e:
            print(f"  ❌ Database setup failed: {e}")
            return False

        return True

    def start_airflow(self):
        """Start Apache Airflow"""
        print("\n⏱️ Starting Apache Airflow...")

        try:
            # Check if Airflow is already running
            result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'],
                                  capture_output=True, text=True)

            if 'airflow-webserver' in result.stdout:
                print("  ⚠️  Airflow is already running")
            else:
                # Start Airflow
                print("  Starting Airflow containers...")
                subprocess.run([
                    'docker-compose', '-f', 'docker-compose.airflow.yml',
                    '--env-file', '.env.airflow', 'up', '-d'
                ], cwd=self.project_root, check=True)

                print("  ⏳ Waiting for Airflow to initialize (40 seconds)...")
                time.sleep(40)

            self.services['airflow'] = True
            print("  ✅ Airflow is ready at http://localhost:8080")

        except Exception as e:
            print(f"  ❌ Failed to start Airflow: {e}")
            return False

        return True

    def start_metabase(self):
        """Start Metabase"""
        print("\n📊 Starting Metabase...")

        try:
            # Check if Metabase is already running
            result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'],
                                  capture_output=True, text=True)

            if 'metabase' in result.stdout:
                print("  ⚠️  Metabase is already running")
            else:
                # Start Metabase
                print("  Starting Metabase containers...")
                subprocess.run([
                    'docker-compose', '-f', 'docker-compose.metabase.yml', 'up', '-d'
                ], cwd=self.project_root, check=True)

                print("  ⏳ Waiting for Metabase to initialize (30 seconds)...")
                time.sleep(30)

                # Run setup script
                print("  Configuring Metabase...")
                subprocess.run(['python', 'scripts/setup_metabase.py'],
                             cwd=self.project_root, check=True)

            self.services['metabase'] = True
            print("  ✅ Metabase is ready at http://localhost:3000")

        except Exception as e:
            print(f"  ❌ Failed to start Metabase: {e}")
            return False

        return True

    def generate_reports(self):
        """Generate initial reports"""
        print("\n📄 Generating initial reports...")

        try:
            subprocess.run(['python', '-m', 'src.visualization.report_generator', '--all'],
                          cwd=self.project_root, check=True)

            self.services['reports'] = True
            print("  ✅ Reports generated in 'reports/' directory")

        except Exception as e:
            print(f"  ❌ Failed to generate reports: {e}")
            return False

        return True

    def open_dashboards(self):
        """Open dashboards in browser"""
        print("\n🌐 Opening dashboards...")

        dashboards = {
            'Apache Airflow': 'http://localhost:8080',
            'Metabase': 'http://localhost:3000',
            'Reports Index': f'file://{self.project_root}/reports/index.html'
        }

        for name, url in dashboards.items():
            try:
                webbrowser.open(url)
                print(f"  ✅ Opened {name}: {url}")
            except:
                print(f"  ⚠️  Could not open {name}")

    def print_summary(self):
        """Print deployment summary"""
        print("\n" + "="*60)
        print("🎉 E-COMMERCE ANALYTICS PLATFORM DEPLOYMENT COMPLETE")
        print("="*60)

        print("\n📊 DEPLOYMENT STATUS:")
        for service, status in self.services.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {service.replace('_', ' ').title()}")

        print("\n🔗 ACCESS LINKS:")
        print("  • Apache Airflow: http://localhost:8080")
        print("     Username: admin, Password: admin")
        print("  • Metabase: http://localhost:3000")
        print("     Email: admin@ecommerce.com, Password: EcommerceAdmin2025!")
        print(f"  • Reports: file://{self.project_root}/reports/index.html")

        print("\n📋 NEXT STEPS:")
        print("  1. Set up Power BI Desktop using connection string in powerbi/")
        print("  2. Configure email alerts in Airflow")
        print("  3. Set up scheduled reports in Metabase")
        print("  4. Monitor pipeline performance")

        print("\n⚙️  MANAGEMENT COMMANDS:")
        print("  • Stop all services: docker-compose -f docker-compose.*.yml down")
        print("  • View logs: docker-compose -f docker-compose.airflow.yml logs -f")
        print("  • Update data: python scripts/run_etl.py")
        print("  • Generate new reports: python -m src.visualization.report_generator")

    def deploy_all(self):
        """Run complete deployment"""
        print("="*60)
        print("🚀 DEPLOYING E-COMMERCE ANALYTICS PLATFORM")
        print("="*60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Project: {self.project_root}")
        print("="*60)

        # Check prerequisites
        if not self.check_prerequisites():
            print("\n❌ Please install missing prerequisites first.")
            sys.exit(1)

        # Setup environment
        self.setup_environment()

        # Setup database
        if not self.setup_database():
            print("\n❌ Database setup failed. Check your DB connection.")
            sys.exit(1)

        # Start services
        self.start_airflow()
        self.start_metabase()

        # Generate reports
        self.generate_reports()

        # Open dashboards
        self.open_dashboards()

        # Print summary
        self.print_summary()

def main():
    """Main deployment function"""
    deployer = EcommercePlatformDeployer()

    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'database':
            deployer.setup_database()
        elif command == 'airflow':
            deployer.start_airflow()
        elif command == 'metabase':
            deployer.start_metabase()
        elif command == 'reports':
            deployer.generate_reports()
        elif command == 'status':
            deployer.print_summary()
        elif command == 'open':
            deployer.open_dashboards()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: database, airflow, metabase, reports, status, open")
    else:
        # Full deployment
        deployer.deploy_all()

if __name__ == "__main__":
    main()
