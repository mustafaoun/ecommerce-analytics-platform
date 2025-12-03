# src/etl/data_generator.py
import pandas as pd
import numpy as np
from faker import Faker
import uuid
from datetime import datetime, timedelta
import random
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EcommerceDataGenerator:
    def __init__(self, seed=42):
        self.fake = Faker()
        Faker.seed(seed)
        np.random.seed(seed)
        random.seed(seed)
        
        # Predefine some realistic values
        self.countries = ['USA', 'UK', 'Canada', 'Australia', 'Germany', 'France', 'Japan', 'Brazil']
        self.channels = ['organic', 'google_ads', 'facebook', 'instagram', 'email', 'referral']
        
        # Product categories with realistic distribution
        self.product_categories = {
            'Electronics': {
                'subcategories': ['Smartphones', 'Laptops', 'Headphones', 'Tablets', 'Cameras'],
                'price_range': (100, 2000),
                'popularity': 0.35
            },
            'Fashion': {
                'subcategories': ["Men's Clothing", "Women's Clothing", 'Shoes', 'Accessories'],
                'price_range': (20, 500),
                'popularity': 0.25
            },
            'Home & Garden': {
                'subcategories': ['Furniture', 'Kitchen', 'Decor', 'Lighting'],
                'price_range': (30, 1500),
                'popularity': 0.20
            },
            'Books': {
                'subcategories': ['Fiction', 'Non-Fiction', "Children's", 'Educational'],
                'price_range': (5, 100),
                'popularity': 0.10
            },
            'Sports': {
                'subcategories': ['Outdoor', 'Fitness', 'Team Sports', 'Camping'],
                'price_range': (15, 800),
                'popularity': 0.10
            }
        }
        
        # Pre-generate some common product names
        self.product_names = {
            'Electronics': ['iPhone', 'MacBook', 'AirPods', 'Galaxy', 'ThinkPad', 'iPad', 'Canon', 'Sony'],
            'Fashion': ['T-Shirt', 'Jeans', 'Dress', 'Sneakers', 'Jacket', 'Handbag', 'Watch'],
            'Home & Garden': ['Sofa', 'Chair', 'Lamp', 'Table', 'Cookware', 'Bedding', 'Vase'],
            'Books': ['Novel', 'Guide', 'Biography', 'Textbook', 'Cookbook', 'Comic'],
            'Sports': ['Dumbbell', 'Tent', 'Basketball', 'Yoga Mat', 'Bicycle', 'Helmet']
        }
    
    def generate_users(self, n: int = 1000) -> pd.DataFrame:
        """Generate user data with realistic signup patterns"""
        logger.info(f"Generating {n} users...")
        
        users = []
        for i in range(n):
            # Create signup date with more recent bias (most signups in last 6 months)
            if i < n * 0.6:  # 60% of users signed up in last 6 months
                signup_date = self.fake.date_between(start_date='-180d', end_date='today')
            else:
                signup_date = self.fake.date_between(start_date='-2y', end_date='-180d')
            
            # Country distribution: more from USA
            country_weights = [0.4, 0.15, 0.1, 0.08, 0.07, 0.06, 0.05, 0.09]
            
            # Channel distribution: organic and google_ads are most common
            channel_weights = [0.3, 0.25, 0.2, 0.1, 0.1, 0.05]
            
            user_data = {
                'user_id': str(uuid.uuid4()),
                'email': self.fake.email(),
                'first_name': self.fake.first_name(),
                'last_name': self.fake.last_name(),
                'signup_date': signup_date,
                'country': np.random.choice(self.countries, p=country_weights),
                'city': self.fake.city(),
                'acquisition_channel': np.random.choice(self.channels, p=channel_weights),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            users.append(user_data)
        
        return pd.DataFrame(users)
    
    def generate_products(self, n: int = 200) -> pd.DataFrame:
        """Generate product catalog with realistic pricing"""
        logger.info(f"Generating {n} products...")
        
        products = []
        categories = list(self.product_categories.keys())
        
        # Calculate weights for categories based on popularity
        category_weights = [self.product_categories[cat]['popularity'] for cat in categories]
        
        for _ in range(n):
            # Choose category based on popularity
            category = np.random.choice(categories, p=category_weights)
            category_info = self.product_categories[category]
            
            subcategory = np.random.choice(category_info['subcategories'])
            
            # Generate realistic price based on category
            min_price, max_price = category_info['price_range']
            
            # Cost is 40-70% of price for realistic margin
            price = round(np.random.uniform(min_price, max_price), 2)
            cost = round(price * np.random.uniform(0.4, 0.7), 2)
            
            # Create product name
            base_names = self.product_names.get(category, ['Product'])
            product_name = f"{np.random.choice(base_names)} {self.fake.word().capitalize()} {random.randint(1, 20)}"
            
            product_data = {
                'product_id': str(uuid.uuid4()),
                'name': product_name,
                'category': category,
                'subcategory': subcategory,
                'price': price,
                'cost': cost,
                'description': self.fake.text(max_nb_chars=200),
                'created_at': self.fake.date_time_between(start_date='-3y', end_date='-6m'),
                'updated_at': self.fake.date_time_between(start_date='-3y', end_date='-6m')
            }
            products.append(product_data)
        
        return pd.DataFrame(products)
    
    def generate_orders(self, users_df: pd.DataFrame, products_df: pd.DataFrame, 
                       n_orders: int = 5000) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generate orders with realistic patterns"""
        logger.info(f"Generating {n_orders} orders...")
        
        orders = []
        order_items = []
        
        # Create user_id list weighted by signup date (recent users are more active)
        user_ids = users_df['user_id'].values
        signup_dates = users_df['signup_date'].values
        
        # Calculate user activity weights (more recent signups = more active)
        user_weights = []
        for signup_date in signup_dates:
            days_since_signup = (datetime.now().date() - signup_date).days
            if days_since_signup < 30:
                weight = 5.0  # Very active (signed up < 30 days ago)
            elif days_since_signup < 90:
                weight = 3.0  # Active (signed up < 90 days ago)
            elif days_since_signup < 180:
                weight = 2.0  # Somewhat active
            else:
                weight = 1.0  # Less active
            
            # Adjust for acquisition channel
            user_weights.append(weight)
        
        user_weights = np.array(user_weights) / sum(user_weights)
        
        product_ids = products_df['product_id'].values
        product_prices = dict(zip(products_df['product_id'], products_df['price']))
        
        for i in range(n_orders):
            # Choose user based on weights
            user_idx = np.random.choice(len(user_ids), p=user_weights)
            user_id = user_ids[user_idx]
            
            # Generate order date (more recent bias)
            if i < n_orders * 0.7:  # 70% of orders in last 3 months
                order_date = self.fake.date_time_between(start_date='-90d', end_date='now')
            else:
                order_date = self.fake.date_time_between(start_date='-1y', end_date='-90d')
            
            # More orders on weekends
            if order_date.weekday() >= 5:  # Saturday or Sunday
                # Increase probability of orders on weekends
                order_date = order_date.replace(hour=np.random.choice([12, 13, 14, 15, 16, 17, 18, 19, 20]))
            else:
                order_date = order_date.replace(hour=np.random.choice([9, 10, 11, 12, 13, 14, 15, 16, 17, 18]))
            
            order_id = str(uuid.uuid4())
            
            # Determine number of items in order (most orders have 1-3 items)
            n_items = np.random.choice([1, 2, 3, 4, 5], p=[0.5, 0.3, 0.1, 0.05, 0.05])
            
            order_total = 0
            items_in_order = []
            
            for _ in range(n_items):
                product_id = np.random.choice(product_ids)
                quantity = np.random.randint(1, 4)  # Usually 1-3 of same item
                price = product_prices[product_id]
                
                # Occasionally apply discounts to individual items
                if np.random.random() < 0.1:  # 10% of items have discount
                    price = round(price * np.random.uniform(0.7, 0.95), 2)
                
                items_in_order.append({
                    'order_item_id': None,  # Auto-generated
                    'order_id': order_id,
                    'product_id': product_id,
                    'quantity': quantity,
                    'price_at_time': price
                })
                
                order_total += price * quantity
            
            # Apply order-level discount (10% of orders get 10-20% discount)
            if np.random.random() < 0.1:
                discount = np.random.uniform(0.1, 0.2)
                order_total = round(order_total * (1 - discount), 2)
            
            # Add shipping cost for large orders
            if n_items > 3:
                order_total += 9.99
            
            # Get user's country for shipping
            user_row = users_df[users_df['user_id'] == user_id].iloc[0]
            user_country = user_row['country']
            user_city = user_row['city']
            
            orders.append({
                'order_id': order_id,
                'user_id': user_id,
                'order_date': order_date,
                'total_amount': round(order_total, 2),
                'status': np.random.choice(['completed', 'refunded'], p=[0.85, 0.15]),
                'shipping_country': user_country,
                'shipping_city': user_city,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
            
            order_items.extend(items_in_order)
        
        return pd.DataFrame(orders), pd.DataFrame(order_items)
    
    def generate_events(self, users_df: pd.DataFrame, products_df: pd.DataFrame, 
                       n_events: int = 20000) -> pd.DataFrame:
        """Generate user events (page views, add to cart, purchase)"""
        logger.info(f"Generating {n_events} events...")
        
        events = []
        
        user_ids = users_df['user_id'].values
        product_ids = products_df['product_id'].values
        
        # Create some session IDs
        sessions = [str(uuid.uuid4())[:8] for _ in range(1000)]
        
        for i in range(n_events):
            user_id = np.random.choice(user_ids)
            
            # Generate timestamp with realistic distribution (more in evenings)
            event_time = self.fake.date_time_between(start_date='-90d', end_date='now')
            
            # Adjust hour distribution: more events in evening
            hour_weights = [0.02] * 8 + [0.04] * 4 + [0.05] * 4 + [0.06] * 4 + [0.04] * 4
            hour_weights = np.array(hour_weights) / np.sum(hour_weights)  # Normalize to sum=1
            event_hour = np.random.choice(range(24), p=hour_weights)
            event_time = event_time.replace(hour=event_hour, 
                                          minute=np.random.randint(0, 60),
                                          second=np.random.randint(0, 60))
            
            # Event types with realistic distribution
            event_type = np.random.choice(
                ['page_view', 'add_to_cart', 'purchase'],
                p=[0.8, 0.15, 0.05]
            )
            
            # For page views, sometimes no product, sometimes with product
            if event_type == 'page_view':
                product_id = np.random.choice(product_ids) if np.random.random() < 0.7 else None
            else:
                product_id = np.random.choice(product_ids)
            
            events.append({
                'event_id': str(uuid.uuid4()),
                'user_id': user_id,
                'event_type': event_type,
                'product_id': product_id,
                'timestamp': event_time,
                'session_id': np.random.choice(sessions),
                'created_at': datetime.now()
            })
        
        return pd.DataFrame(events)
    
    def generate_all_data(self):
        """Generate all data and return as DataFrames"""
        logger.info("Starting data generation...")
        
        users_df = self.generate_users(1000)
        products_df = self.generate_products(200)
        orders_df, order_items_df = self.generate_orders(users_df, products_df, 5000)
        events_df = self.generate_events(users_df, products_df, 20000)
        
        logger.info("✅ Data generation complete!")
        logger.info(f"  Users: {len(users_df)}")
        logger.info(f"  Products: {len(products_df)}")
        logger.info(f"  Orders: {len(orders_df)}")
        logger.info(f"  Order Items: {len(order_items_df)}")
        logger.info(f"  Events: {len(events_df)}")
        
        return {
            'users': users_df,
            'products': products_df,
            'orders': orders_df,
            'order_items': order_items_df,
            'events': events_df
        }

# Quick test function
if __name__ == "__main__":
    generator = EcommerceDataGenerator()
    data = generator.generate_all_data()
    
    # Save to CSV for inspection
    os.makedirs('data/generated', exist_ok=True)
    for table_name, df in data.items():
        filepath = f"data/generated/{table_name}.csv"
        df.to_csv(filepath, index=False)
        print(f"Saved {len(df)} rows to {filepath}")
    
    print("\n✅ Sample data:")
    print(data['users'].head(3))
    print(f"\nDate range: {data['orders']['order_date'].min()} to {data['orders']['order_date'].max()}")