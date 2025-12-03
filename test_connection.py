import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database='postgres',
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        sslmode='require'  # مطلوب لـ Supabase
    )
    print("✅ Connection successful with Pooler!")
    
    # Test query بسيط للتأكيد
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"DB Version: {version}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")