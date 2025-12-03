import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class DataLoader:
    def __init__(self):
        # Create SQLAlchemy engine
        self.db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@" \
                      f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?sslmode=require"
        self.engine = create_engine(self.db_url, pool_size=10, max_overflow=20)
    
    def load_dataframe(self, df: pd.DataFrame, table_name: str, 
                       if_exists: str = 'append', chunk_size: int = 1000) -> bool:
        """
        Load a DataFrame to PostgreSQL table
        
        Args:
            df: DataFrame to load
            table_name: Target table name
            if_exists: 'fail', 'replace', or 'append'
            chunk_size: Number of rows to insert at once
        
        Returns:
            bool: Success status
        """
        try:
            # FIX: Added loaded_at for all tables (as per schema)
            if 'loaded_at' not in df.columns:
                df['loaded_at'] = datetime.now()
            
            logger.info(f"Loading {len(df)} rows to {table_name}...")
            
            # Use to_sql with chunking for large datasets
            df.to_sql(
                table_name,
                self.engine,
                if_exists=if_exists,
                index=False,
                method='multi',
                chunksize=chunk_size
            )
            
            logger.info(f"✅ Successfully loaded {len(df)} rows to {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load data to {table_name}: {e}")
            return False
    
    def load_from_csv(self, csv_path: str, table_name: str, 
                      if_exists: str = 'append') -> bool:
        """
        Load data from CSV file to database
        """
        try:
            logger.info(f"Loading CSV from {csv_path} to {table_name}...")
            
            # Read CSV in chunks for memory efficiency
            chunk_size = 10000
            total_rows = 0
            
            for chunk in pd.read_csv(csv_path, chunksize=chunk_size):
                # We need to set if_exists for the first chunk to the requested value
                current_if_exists = if_exists if total_rows == 0 else 'append'

                success = self.load_dataframe(chunk, table_name, if_exists=current_if_exists)
                if success:
                    total_rows += len(chunk)
                    logger.info(f"  Processed {total_rows} rows...")
                else:
                    return False
                
            logger.info(f"✅ Loaded {total_rows} rows from {csv_path} to {table_name}")
            return True
            
        except FileNotFoundError:
            logger.error(f"❌ CSV file not found: {csv_path}")
            return False
        except Exception as e:
            logger.error(f"❌ Error loading CSV: {e}")
            return False
    
    def truncate_table(self, table_name: str) -> bool:
        """Truncate a table (delete all rows)"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
                conn.commit()
                logger.info(f"✅ Truncated table: {table_name}")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to truncate {table_name}: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> dict:
        """Get information about a table"""
        try:
            with self.engine.connect() as conn:
                # Get row count
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = count_result.fetchone()[0]
                
                # Get column names
                columns_result = conn.execute(
                    text(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                    """)
                )
                columns = [f"{row[0]} ({row[1]})" for row in columns_result]
                
                return {
                    'table': table_name,
                    'row_count': row_count,
                    'columns': columns
                }
        except Exception as e:
            logger.error(f"❌ Failed to get info for {table_name}: {e}")
            return {}
    
    def run_etl_pipeline(self, data_dict: dict, truncate_first: bool = True) -> bool:
        """
        Run complete ETL pipeline
        
        Args:
            data_dict: Dictionary of table_name: DataFrame pairs
            truncate_first: Whether to truncate tables before loading
        
        Returns:
            bool: Overall success status
        """
        logger.info("🚀 Starting ETL pipeline...")
        
        # Define load order (respect foreign key constraints)
        load_order = ['users', 'products', 'orders', 'order_items', 'events', 'marketing_campaigns']
        
        all_success = True
        
        for table_name in load_order:
            if table_name in data_dict:
                df = data_dict[table_name]
                
                # Truncate if requested
                if truncate_first:
                    self.truncate_table(table_name)
                
                # Load data
                success = self.load_dataframe(df, table_name, if_exists='append')
                
                if not success:
                    all_success = False
                    logger.error(f"❌ ETL pipeline failed at table: {table_name}")
                    break
        
        if all_success:
            logger.info("✅ ETL pipeline completed successfully!")
            
            # Print summary
            print("\n📊 ETL Pipeline Summary:")
            print("-" * 40)
            for table_name in load_order:
                if table_name in data_dict:
                    info = self.get_table_info(table_name)
                    if info:
                        print(f"{table_name:15} | {info['row_count']:>8} rows")
        else:
            logger.error("❌ ETL pipeline failed!")
        
        return all_success

# Singleton instance
loader = DataLoader()