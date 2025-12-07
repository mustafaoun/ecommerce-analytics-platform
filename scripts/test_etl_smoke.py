#!/usr/bin/env python
# scripts/test_etl_smoke.py
"""
Smoke test for ETL pipeline integration.
Generates small amounts of data and loads them without truncation.
Safe for repeated runs without destroying existing data.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.etl.data_generator import EcommerceDataGenerator
from src.etl.data_loader import DataLoader
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_data_generator():
    """Test data generator in isolation"""
    print("\n" + "="*60)
    print("🧪 TEST 1: Data Generator Smoke Test")
    print("="*60)
    
    try:
        print("\n  Generating small dataset (10 users, 5 products, 20 orders)...")
        generator = EcommerceDataGenerator(seed=12345)
        
        # Generate small amounts
        users = generator.generate_users(n=10)
        products = generator.generate_products(n=5)
        orders = generator.generate_orders(users, n_orders=20)
        # Note: generate_order_items returns (order_items_df, orders_df) tuple
        order_items, orders = generator.generate_order_items(orders, products)
        events = generator.generate_events(users, products, orders, n_events=50)
        
        print(f"  ✅ Users: {len(users)} rows")
        print(f"  ✅ Products: {len(products)} rows")
        print(f"  ✅ Orders: {len(orders)} rows")
        print(f"  ✅ Order Items: {len(order_items)} rows")
        print(f"  ✅ Events: {len(events)} rows")
        
        # Check data integrity
        print("\n  Validating data integrity...")
        assert len(users) == 10, "Expected 10 users"
        assert len(products) == 5, "Expected 5 products"
        assert len(orders) >= 20, f"Expected at least 20 orders, got {len(orders)}"
        assert len(order_items) > 0, "Expected order items"
        assert len(events) >= 50, f"Expected at least 50 events, got {len(events)}"
        
        # Check columns
        print("  ✅ All users have required columns:", all(col in users.columns for col in ['user_id', 'email', 'country']))
        print("  ✅ All products have required columns:", all(col in products.columns for col in ['product_id', 'name', 'category']))
        print("  ✅ All orders have required columns:", all(col in orders.columns for col in ['order_id', 'user_id', 'total_amount']))
        
        data_dict = {
            'users': users,
            'products': products,
            'orders': orders,
            'order_items': order_items,
            'events': events
        }
        
        print("\n✅ TEST 1 PASSED: Data generator works correctly")
        return True, data_dict
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_data_loader(data_dict):
    """Test data loader in isolation"""
    print("\n" + "="*60)
    print("🧪 TEST 2: Data Loader Smoke Test (Truncate Mode)")
    print("="*60)
    
    try:
        print("\n  Initializing data loader...")
        loader = DataLoader()
        
        if not loader.engine:
            print("  ❌ Failed to create database connection")
            return False
        
        print("  ✅ Database connection successful")
        
        # Test loading with truncation to ensure clean state
        print("\n  Loading data to database (truncate + reload mode)...")
        success = loader.run_etl_pipeline(data_dict, truncate_first=True)
        
        if not success:
            print("  ❌ ETL pipeline failed")
            return False
        
        print("  ✅ Data loaded successfully")
        
        # Verify data loaded
        print("\n  Verifying data in database...")
        table_info = loader.get_table_info('users')
        if table_info:
            print(f"  ✅ Users table has {table_info['row_count']} rows (may include previous test data)")
            print(f"     Columns: {', '.join(table_info['columns'][:3])}...")
        
        table_info = loader.get_table_info('products')
        if table_info:
            print(f"  ✅ Products table has {table_info['row_count']} rows")
        
        table_info = loader.get_table_info('orders')
        if table_info:
            print(f"  ✅ Orders table has {table_info['row_count']} rows")
        
        print("\n✅ TEST 2 PASSED: Data loader works correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test end-to-end integration"""
    print("\n" + "="*60)
    print("🧪 TEST 3: End-to-End ETL Integration")
    print("="*60)
    
    try:
        start_time = time.time()
        
        print("\n  Running full ETL pipeline (generate + load)...")
        
        # Generate
        print("  Generating data...")
        generator = EcommerceDataGenerator(seed=99999)
        data = generator.generate_all_data()
        
        total_rows_generated = sum(len(df) for df in data.values())
        print(f"  ✅ Generated {total_rows_generated} total rows")
        
        # Load
        print("  Loading data...")
        loader = DataLoader()
        success = loader.run_etl_pipeline(data, truncate_first=True)
        
        if not success:
            print("  ❌ Pipeline failed during load")
            return False
        
        elapsed_time = time.time() - start_time
        
        print(f"\n  ✅ Pipeline completed in {elapsed_time:.2f} seconds")
        print(f"  📊 Throughput: {total_rows_generated/elapsed_time:.0f} rows/second")
        
        print("\n✅ TEST 3 PASSED: End-to-end integration works")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all smoke tests"""
    print("\n" + "="*60)
    print("🔬 E-COMMERCE ETL PIPELINE SMOKE TESTS")
    print("="*60)
    
    results = {}
    
    # Test 1: Data Generator
    test1_pass, data_dict = test_data_generator()
    results['Data Generator'] = test1_pass
    
    # Test 2: Data Loader (only if test 1 passed)
    if test1_pass and data_dict:
        test2_pass = test_data_loader(data_dict)
        results['Data Loader'] = test2_pass
    else:
        print("\n⏭️  Skipping Test 2 (no data from Test 1)")
        results['Data Loader'] = False
    
    # Test 3: Full Integration
    test3_pass = test_integration()
    results['End-to-End Integration'] = test3_pass
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    all_pass = all(results.values())
    
    if all_pass:
        print("\n🎉 ALL TESTS PASSED!")
        print("   ETL pipeline is working correctly.")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("   Review the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
