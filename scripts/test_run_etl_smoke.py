# scripts/test_run_etl_smoke.py
"""Smoke test for ETL: generates small datasets and attempts to load them.
This uses small sizes to be fast and non-destructive by default (no truncation).
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.etl.data_generator import EcommerceDataGenerator
from src.etl.data_loader import DataLoader


def main():
    print("🔬 ETL Smoke Test")

    gen = EcommerceDataGenerator(seed=123)
    data = gen.generate_all_data(n_users=50, n_products=20, n_orders=200, n_events=1000)

    loader = DataLoader()
    if not loader.engine:
        print("❌ DataLoader engine not created. Check DB env vars.")
        return 1

    print("ℹ️ Running ETL pipeline (no truncate)...")
    success = loader.run_etl_pipeline(data, truncate_first=False)

    if success:
        print("✅ Smoke ETL succeeded")
        return 0
    else:
        print("❌ Smoke ETL failed")
        return 2

if __name__ == '__main__':
    sys.exit(main())
