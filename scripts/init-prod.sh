#!/bin/bash

# Ecommerce Analytics Platform - Production Initialization Script
# Run database migrations and load initial data on startup

set -e

echo "🚀 Starting Ecommerce Analytics Platform..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
while ! pg_isready -h $DB_HOST -U $DB_USER; do
  sleep 1
done
echo "✅ PostgreSQL is ready"

# Create database schema
echo "🏗️  Creating database schema..."
python scripts/create_schema.py

# Load sample data
echo "📊 Loading sample data..."
python -c "
from src.etl.data_generator import (
    generate_users, generate_products, generate_orders,
    generate_order_items, generate_events, generate_marketing_campaigns
)
from src.database.connection import get_engine
from src.etl.data_loader import DataLoader

engine = get_engine()
loader = DataLoader(f'postgresql://{os.getenv(\"DB_USER\")}:{os.getenv(\"DB_PASSWORD\")}@{os.getenv(\"DB_HOST\")}:{os.getenv(\"DB_PORT\")}/{os.getenv(\"DB_NAME\")}')

print('🔄 Generating sample data...')
users = generate_users(n=100)
products = generate_products(n=50)
orders, _ = generate_orders(n=200, users_df=users)
order_items, orders = generate_order_items(orders, products, n=1000)
events = generate_events(n=645, users_df=users)
campaigns = generate_marketing_campaigns(n=10)

print('📤 Loading data to PostgreSQL...')
loader.load_data(users, 'users', truncate_first=True)
loader.load_data(products, 'products', truncate_first=True)
loader.load_data(orders, 'orders', truncate_first=True)
loader.load_data(order_items, 'order_items', truncate_first=True)
loader.load_data(events, 'events', truncate_first=True)
loader.load_data(campaigns, 'marketing_campaigns', truncate_first=True)

print('✅ Data loaded successfully!')
"

echo "✅ Production initialization complete!"
echo "🌐 Metabase available at http://localhost:3000"
echo "📊 API available at http://localhost:5000"
