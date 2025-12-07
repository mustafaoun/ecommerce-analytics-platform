import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432,
    user='ecommerce_user', password='ecommerce_password',
    dbname='ecommerce'
)
cursor = conn.cursor()

tables = ['users', 'products', 'orders', 'order_items', 'events']
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"{table}: {count} rows")

conn.close()
