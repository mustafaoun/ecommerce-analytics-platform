# scripts/run_etl.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.etl.data_generator import EcommerceDataGenerator
from src.etl.data_loader import DataLoader
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main ETL pipeline execution"""
    print("🚀 E-commerce Analytics ETL Pipeline")
    print("=" * 50)
    
    start_time = time.time()
    
    try:
        # Step 1: Generate data
        print("\n1️⃣ Generating synthetic data...")
        generator = EcommerceDataGenerator(seed=42)
        data = generator.generate_all_data()
        
        # Step 2: Load to database
        print("\n2️⃣ Loading data to PostgreSQL...")
        loader = DataLoader()
        
        # Test connection first
        if not loader.engine:
            print("❌ Database connection failed!")
            return False
        
        # Run ETL pipeline
        success = loader.run_etl_pipeline(data, truncate_first=True)
        
        if success:
            print("\n" + "=" * 50)
            print("✅ ETL PIPELINE COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            
            # Calculate and display statistics
            elapsed_time = time.time() - start_time
            total_rows = sum(len(df) for df in data.values())
            
            print(f"\n📊 Statistics:")
            print(f"  • Total time: {elapsed_time:.2f} seconds")
            print(f"  • Total rows processed: {total_rows:,}")
            print(f"  • Rows per second: {total_rows/elapsed_time:.0f}")
            
            # Display sample queries
            print(f"\n🔍 Sample queries you can run:")
            print(f"  SELECT COUNT(*) FROM users;")
            print(f"  SELECT category, COUNT(*) FROM products GROUP BY category;")
            print(f"  SELECT DATE(order_date) as day, SUM(total_amount) FROM orders GROUP BY day ORDER BY day DESC LIMIT 7;")
            
            return True
        else:
            print("❌ ETL pipeline failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Pipeline error: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)