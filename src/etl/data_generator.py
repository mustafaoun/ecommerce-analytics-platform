# src/etl/data_generator.py
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
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            products.append(product_data)
       
        return pd.DataFrame(products)
   
    def generate_all_data(self, n_users: int = 1000, n_products: int = 200) -> Dict[str, pd.DataFrame]:
        """Generate all synthetic data: users and products"""
        logger.info("Generating all synthetic data...")
        users = self.generate_users(n_users)
        products = self.generate_products(n_products)
        return {
            'users': users,
            'products': products
        }