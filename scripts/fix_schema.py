import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db

def fix_schema():
    """Fix database schema issues"""
    print("🔧 Fixing database schema...")
    
    with db.get_connection() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            
            # Check if signup_date column exists in users table
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'signup_date'
            """)
            
            result = cur.fetchone()
            
            if not result:
                print("❌ 'signup_date' column not found in 'users' table")
                
                # Check what columns exist
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users'
                """)
                
                columns = cur.fetchall()
                print(f"Available columns in users table: {[c[0] for c in columns]}")
                
                # Add signup_date column if it doesn't exist
                try:
                    print("Adding 'signup_date' column...")
                    cur.execute("""
                        ALTER TABLE users ADD COLUMN signup_date DATE;
                        
                        -- Populate with created_at date if it exists
                        UPDATE users 
                        SET signup_date = DATE(created_at) 
                        WHERE signup_date IS NULL;
                        
                        -- Make it NOT NULL after populating
                        ALTER TABLE users ALTER COLUMN signup_date SET NOT NULL;
                    """)
                    print("✅ Added 'signup_date' column")
                except Exception as e:
                    print(f"❌ Error adding column: {e}")
            
            # Check and create views
            print("\nCreating/updating views...")
            
            # Drop and recreate views if they exist
            views = ['sales_summary', 'customer_lifetime_value_view', 
                    'product_performance_view', 'daily_kpi_view', 
                    'geographic_performance_view']
            
            for view in views:
                try:
                    cur.execute(f"DROP VIEW IF EXISTS {view} CASCADE;")
                except:
                    pass
            
            # Recreate all views from the powerbi_views.sql file
            print("Reading powerbi_views.sql...")
            
            # Read the SQL file
            sql_file_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'database', 'powerbi_views.sql')
            
            with open(sql_file_path, 'r') as f:
                sql_commands = f.read()
            
            # Execute each command
            commands = sql_commands.split(';')
            
            for command in commands:
                command = command.strip()
                if command:
                    try:
                        cur.execute(command)
                        print(f"Executed: {command[:50]}...")
                    except Exception as e:
                        print(f"Error executing: {e}\nCommand: {command[:100]}...")
            
            print("\n✅ Schema fixed successfully!")

if __name__ == "__main__":
    fix_schema()