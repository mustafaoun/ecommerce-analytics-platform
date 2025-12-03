# src/etl/data_generator_incremental.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid
import logging
import os
from dotenv import load_dotenv
from .data_generator import EcommerceDataGenerator  # Reuse base generator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def generate_daily_events(target_date: datetime, n_users: int = 50, n_events: int = 1000):
    """
    Generate incremental events for a specific date
    """
    logger.info(f"Generating incremental data for {target_date.date()}...")
    
    # Use the existing generator for base data
    generator = EcommerceDataGenerator(seed=int(target_date.timestamp()))
    
    # Get existing users from database (in production – here simulate with small generate)
    users = generator.generate_users(n=n_users)
    
    # Get existing products (simulate)
    products = generator.generate_products(n=30)
    
    # Generate events for the target date
    events = []
    product_ids = products['product_id'].values
    user_ids = users['user_id'].values
    
    for i in range(n_events):
        user_id = np.random.choice(user_ids)
        
        # Generate event time within the target date
        event_time = target_date.replace(
            hour=np.random.choice(range(24), p=[0.01]*8 + [0.02]*4 + [0.03]*4 + [0.04]*4 + [0.02]*4),
            minute=np.random.randint(0, 60),
            second=np.random.randint(0, 60)
        )
        
        # Event types with realistic distribution
        event_type = np.random.choice(
            ['page_view', 'add_to_cart', 'purchase'],
            p=[0.8, 0.15, 0.05]
        )
        
        # For page views, sometimes no product
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
            'session_id': str(uuid.uuid4())[:8],
            'loaded_at': datetime.now()
        })
    
    events_df = pd.DataFrame(events)
    
    # Generate orders if there were purchases
    purchases = events_df[events_df['event_type'] == 'purchase']
    
    orders = []
    order_items = []
    
    if not purchases.empty:
        # Group purchases by user to create orders
        for user_id in purchases['user_id'].unique():
            user_purchases = purchases[purchases['user_id'] == user_id]
            
            # Create one order per user per day (simplified)
            order_id = str(uuid.uuid4())
            order_date = target_date.replace(
                hour=np.random.randint(9, 21),
                minute=np.random.randint(0, 60)
            )
            
            # Calculate order total
            order_total = 0
            for _, purchase in user_purchases.iterrows():
                product = products[products['product_id'] == purchase['product_id']].iloc[0]
                quantity = np.random.randint(1, 4)
                price = product['price']
                
                order_items.append({
                    'order_item_id': None,  # Auto
                    'order_id': order_id,
                    'product_id': purchase['product_id'],
                    'quantity': quantity,
                    'price_at_time': price,
                    'created_at': datetime.now()
                })
                
                order_total += price * quantity
            
            # Add shipping for large orders
            if len(order_items) > 3:
                order_total += 9.99
            
            orders.append({
                'order_id': order_id,
                'user_id': user_id,
                'order_date': order_date,
                'total_amount': round(order_total, 2),
                'status': 'completed',
                'shipping_country': users[users['user_id'] == user_id]['country'].values[0],
                'shipping_city': users[users['user_id'] == user_id]['city'].values[0],
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
    
    logger.info(f"Generated {len(events)} events, {len(orders)} orders for {target_date.date()}")
    
    return {
        'events': events_df,
        'orders': pd.DataFrame(orders) if orders else pd.DataFrame(),
        'order_items': pd.DataFrame(order_items) if order_items else pd.DataFrame()
    }

def generate_weekly_aggregations(start_date: datetime):
    """Generate weekly aggregated data"""
    logger.info(f"Generating weekly aggregations from {start_date.date()}...")
    
    # Generate 7 days of data
    weekly_data = []
    for i in range(7):
        day = start_date + timedelta(days=i)
        daily_data = generate_daily_events(day, n_events=500)
        weekly_data.append(daily_data)
    
    # Combine all data
    all_events = pd.concat([d['events'] for d in weekly_data])
    all_orders = pd.concat([d['orders'] for d in weekly_data if not d['orders'].empty])
    all_order_items = pd.concat([d['order_items'] for d in weekly_data if not d['order_items'].empty])
    
    return {
        'events': all_events,
        'orders': all_orders,
        'order_items': all_order_items
    }