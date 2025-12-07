import pandas as pd

import numpy as np

from faker import Faker

import uuid

from datetime import datetime, timedelta

import random

from typing import Dict, List, Tuple

import logging

import os



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

        used_emails = set()  # Track unique emails

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

            

            # Generate unique email

            email = None

            attempts = 0

            while email is None and attempts < 10:

                email = self.fake.email()

                attempts += 1

                if email in used_emails:

                    email = None

            if email is None:

                email = f"user_{i}@{self.fake.domain_name()}"  # Fallback

            used_emails.add(email)

            

            user_data = {

                'user_id': str(uuid.uuid4()),

                'email': email,

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

            base_names = self.product_names.get(category, [])

            if base_names:

                product_name = f"{np.random.choice(base_names)} {subcategory} {self.fake.word()}"

            else:

                product_name = f"{subcategory} {self.fake.word()}"

            

            product_data = {

                'product_id': str(uuid.uuid4()),

                'name': product_name,

                'category': category,

                'subcategory': subcategory,

                'price': price,

                'cost': cost,

                

                # 🎯 السطر المطلوب لـ stock_quantity

                'stock_quantity': random.randint(50, 500) if category == 'Electronics' else random.randint(100, 1000), 

                

                'created_at': datetime.now(),

                'updated_at': datetime.now()

            }

            products.append(product_data)

        

        return pd.DataFrame(products)



    def generate_orders(self, users_df: pd.DataFrame, n_orders: int = 5000) -> pd.DataFrame:

        """Generate order data, linking them to existing users."""

        if users_df.empty:

            logger.warning("Users DataFrame is empty. Cannot generate orders.")

            return pd.DataFrame()



        logger.info(f"Generating {n_orders} orders...")

        

        orders = []

        user_ids = users_df['user_id'].tolist()

        signup_dates = users_df.set_index('user_id')['signup_date'].to_dict()

        

        start_date_recent = datetime.now() - timedelta(days=180)

        start_date_old = datetime.now() - timedelta(days=730) 

        end_date = datetime.now()

        

        for i in range(n_orders):

            user_index = int(np.power(random.random(), 2) * len(user_ids))

            user_id = user_ids[user_index]

            

            user_signup_date = datetime.combine(signup_dates[user_id], datetime.min.time())

            

            if random.random() < 0.7:

                order_date = self.fake.date_time_between(

                    start_date=max(user_signup_date, start_date_recent), 

                    end_date=end_date

                )

            else:

                order_date = self.fake.date_time_between(

                    start_date=max(user_signup_date, start_date_old), 

                    end_date=start_date_recent

                )

                

            order_data = {

                'order_id': str(uuid.uuid4()),

                'user_id': user_id,

                'order_date': order_date,

                'total_amount': 0.0, # Placeholder

                'status': np.random.choice(['completed', 'shipped', 'cancelled'], p=[0.85, 0.1, 0.05]),

                'shipping_country': self.fake.country(),

                'shipping_city': self.fake.city(),

                'created_at': datetime.now(),

                'updated_at': datetime.now(),

            }

            orders.append(order_data)



        return pd.DataFrame(orders)



    def generate_order_items(self, orders_df: pd.DataFrame, products_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:

        """Generate order items and update the total_amount in the orders DataFrame."""

        if orders_df.empty or products_df.empty:

            logger.warning("Orders or Products DataFrame is empty. Cannot generate order items.")

            return pd.DataFrame(), orders_df

            

        logger.info(f"Generating order items...")

        

        order_items = []

        products_map = products_df.set_index('product_id')['price'].to_dict()

        

        order_totals: Dict[str, float] = {}

        

        for _, order_row in orders_df.iterrows():

            order_id = order_row['order_id']

            num_items = np.random.randint(1, 5) 

            

            order_total = 0.0

            

            selected_product_ids = np.random.choice(

                products_df['product_id'], 

                size=min(num_items, len(products_df)), # Prevent error if num_items > num_products

                replace=False

            )

            

            for product_id in selected_product_ids:

                price_at_time = products_map[product_id] 

                quantity = np.random.randint(1, 4) 

                

                line_total = quantity * price_at_time

                order_total += line_total

                

                item_data = {

                    # order_item_id will be generated by the DB SERIAL key

                    'order_id': order_id,

                    'product_id': product_id,

                    'quantity': quantity,

                    'price_at_time': price_at_time,

                    'created_at': order_row['order_date'] + timedelta(seconds=random.randint(0, 30)),

                }

                order_items.append(item_data)

            

            order_totals[order_id] = round(order_total, 2)

            

        # Update the total_amount in the original orders_df

        orders_df['total_amount'] = orders_df['order_id'].map(order_totals).fillna(0.0)

        

        return pd.DataFrame(order_items), orders_df



    def generate_events(self, users_df: pd.DataFrame, products_df: pd.DataFrame, orders_df: pd.DataFrame, n_events: int = 100000) -> pd.DataFrame:

        """Generate user interaction events (view, cart, purchase)."""

        if users_df.empty:

            logger.warning("Users DataFrame is empty. Cannot generate events.")

            return pd.DataFrame()

            

        logger.info(f"Generating {n_events} events...")

        

        events = []

        user_ids = users_df['user_id'].tolist()

        product_ids = products_df['product_id'].tolist() if not products_df.empty else []

        

        event_types = ['product_view', 'add_to_cart', 'checkout', 'purchase', 'session_start']

        event_weights = [0.4, 0.25, 0.05, 0.05, 0.25] 

        

        # 1. Create Purchase events from existing orders (ensures referential integrity)

        purchase_events = orders_df[['user_id', 'order_date']].copy()

        purchase_events = purchase_events.rename(columns={'order_date': 'timestamp'})

        

        for _, row in purchase_events.iterrows():

            events.append({

                'event_id': str(uuid.uuid4()),

                'user_id': row['user_id'],

                'event_type': 'purchase',

                'product_id': None, # Purchase event is transactional, not product-specific

                'timestamp': row['timestamp'],

                'session_id': str(uuid.uuid4()), 

            })



        # 2. Generate the remaining interaction events

        for _ in range(n_events - len(events)):

            user_id = np.random.choice(user_ids)

            event_type = np.random.choice(event_types, p=event_weights)

            

            product_id = np.random.choice(product_ids) if product_ids and event_type in ['product_view', 'add_to_cart'] else None

            

            timestamp = self.fake.date_time_between(start_date='-180d', end_date='now')

            

            event_data = {

                'event_id': str(uuid.uuid4()),

                'user_id': user_id,

                'event_type': event_type,

                'product_id': product_id,

                'timestamp': timestamp,

                'session_id': str(uuid.uuid4()) if event_type == 'session_start' else self.fake.uuid4(),

            }

            events.append(event_data)

            

        return pd.DataFrame(events).sort_values(by='timestamp').reset_index(drop=True)



    def generate_all_data(self, n_users: int = 1000, n_products: int = 200, n_orders: int = 5000, n_events: int = 100000) -> Dict[str, pd.DataFrame]:

        """Generate all synthetic data: users, products, orders, order_items, and events."""

        logger.info("🚀 Generating all synthetic data...")

        

        # 1. Generate Base Data

        users_df = self.generate_users(n_users)

        products_df = self.generate_products(n_products)

        

        # 2. Generate Transaction Data (requires users)

        orders_df = self.generate_orders(users_df, n_orders)

        

        # 3. Generate Order Items (requires products and updates orders)

        # Note: orders_df is updated in place and returned for the orders table

        order_items_df, orders_df = self.generate_order_items(orders_df, products_df)

        

        # 4. Generate Event Data (requires users, products, and orders)

        events_df = self.generate_events(users_df, products_df, orders_df, n_events)



        logger.info("✅ Data generation complete.")



        return {

            'users': users_df,

            'products': products_df,

            'orders': orders_df,

            'order_items': order_items_df,

            'events': events_df

            # marketing_campaigns data would be generated here if needed

        } 