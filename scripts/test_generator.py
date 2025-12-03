# scripts/test_generator.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.etl.data_generator import EcommerceDataGenerator

def main():
    print("🧪 Testing data generator...")
    
    # Create generator
    generator = EcommerceDataGenerator(seed=42)
    
    # Generate small dataset for testing
    print("Generating test data...")
    test_data = generator.generate_all_data()
    
    # Display sample data
    print("\n📊 Sample Users:")
    print(test_data['users'][['email', 'country', 'acquisition_channel']].head(3))
    
    print("\n📊 Sample Products:")
    print(test_data['products'][['name', 'category', 'price']].head(3))
    
    print("\n📊 Sample Orders:")
    print(test_data['orders'][['order_date', 'total_amount', 'status']].head(3))
    
    print("\n📊 Sample Events:")
    print(test_data['events'][['event_type', 'timestamp']].head(3))
    
    # Save test data
    print("\n💾 Saving test data...")
    os.makedirs('data/test', exist_ok=True)
    
    for table_name, df in test_data.items():
        filepath = f"data/test/{table_name}_test.csv"
        df.to_csv(filepath, index=False)
        print(f"  Saved {filepath} ({len(df)} rows)")
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    main()