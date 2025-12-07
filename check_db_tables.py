import psycopg2

try:
    conn = psycopg2.connect(
        host='localhost', port=5432, 
        user='ecommerce_user', password='ecommerce_password',
        dbname='ecommerce'
    )
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = cursor.fetchall()
    print(f"Tables in 'ecommerce' DB: {len(tables)}")
    for t in tables:
        print(f"  - {t[0]}")
    
    if not tables:
        print("\n⚠️  No tables found! Schema may not be created.")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
