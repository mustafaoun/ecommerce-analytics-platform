# scripts/create_schema.py
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_schema():
    """Create database schema by executing the DDL file"""
    
    # Read the SQL file
    sql_file_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'database', 'schema_ddl.sql')
    
    with open(sql_file_path, 'r') as f:
        sql_commands = f.read()
    
    logger.info("Creating database schema...")
    
    # Split by semicolon to execute commands one by one
    commands = sql_commands.split(';')
    
    with db.get_connection() as conn:
        conn.autocommit = False
        with conn.cursor() as cur:
            for command in commands:
                command = command.strip()
                if command:  # Skip empty commands
                    try:
                        cur.execute(command)
                        logger.info(f"Executed: {command[:50]}...")
                    except Exception as e:
                        logger.error("Schema creation failed")
                        raise
    
        conn.commit()
    logger.info("Schema created successfully")

def test_schema():
    """Test that schema was created correctly"""
    test_queries = [
        "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';",
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
    ]
    
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            for query in test_queries:
                cur.execute(query)
                result = cur.fetchone()
                logger.info(f"Test result: {result}")

if __name__ == "__main__":
    # First, create the database if it doesn't exist
    print("🔧 Setting up database schema...")
    
    if db.test_connection():
        create_schema()
        test_schema()
        print("🎉 Database setup complete!")
    else:
        raise SystemExit("Cannot connect to database. Check your .env settings.")
