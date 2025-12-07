# src/database/connection.py
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from contextlib import contextmanager
from dotenv import load_dotenv
import logging
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class DatabaseConnection:
    def __init__(self):
        self.conn_params = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'sslmode': 'disable'  # Disable SSL for local connections
        }
        # Create SQLAlchemy engine for use with pandas.read_sql_query when possible
        try:
            user = self.conn_params.get('user') or ''
            password = self.conn_params.get('password') or ''
            host = self.conn_params.get('host') or 'localhost'
            port = self.conn_params.get('port') or '5432'
            dbname = self.conn_params.get('database') or ''
            # Disable SSL for local development
            self._engine: Engine = create_engine(
                f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}",
                connect_args={"sslmode": "disable"}
            )
        except Exception:
            self._engine = None
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with auto-close"""
        conn = psycopg2.connect(**self.conn_params)
        try:
            yield conn
        except Exception as e:
            logger.error(f"Database error: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_cursor(self):
        """Get a dictionary cursor"""
        conn = psycopg2.connect(**self.conn_params)
        return conn.cursor(cursor_factory=RealDictCursor)
    
    def test_connection(self):
        """Test if connection works"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version();")
                    version = cur.fetchone()
                    logger.info(f"✅ Connected to PostgreSQL: {version[0]}")
                    return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def execute_query(self, query, params=None, fetch=False):
        """Execute a query and optionally fetch results"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params or ())
                    if fetch:
                        if query.strip().upper().startswith('SELECT'):
                            return cur.fetchall()
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Query failed: {e}\nQuery: {query}")
            return False

    def get_engine(self):
        """Return SQLAlchemy engine if available (or None)."""
        return self._engine

# Singleton instance
db = DatabaseConnection()