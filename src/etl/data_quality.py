# src/etl/data_quality.py
import pandas as pd
from datetime import datetime, timedelta
import logging
from src.database.connection import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataQualityChecker:
    def __init__(self):
        pass
    
    def check_nulls(self, table_name: str, date_column: str = None, date_value: datetime = None):
        """Check for null values in required columns"""
        checks = []
        
        # Define required columns for each table
        required_columns = {
            'users': ['user_id', 'email', 'signup_date'],
            'products': ['product_id', 'name', 'price'],
            'orders': ['order_id', 'user_id', 'order_date', 'total_amount'],
            'events': ['event_id', 'user_id', 'event_type', 'timestamp']
        }
        
        if table_name not in required_columns:
            return [{'table': table_name, 'check': 'null_check', 'status': 'SKIPPED', 'message': 'Table not configured'}]
        
        with db.get_connection() as conn:
            for column in required_columns[table_name]:
                # Build query
                query = f"""
                SELECT COUNT(*) as null_count
                FROM {table_name}
                WHERE {column} IS NULL
                """
                
                if date_column and date_value:
                    query += f" AND {date_column} >= '{date_value.date()}' AND {date_column} < '{date_value.date() + timedelta(days=1)}'"
                
                result = pd.read_sql_query(query, conn)
                null_count = result['null_count'].iloc[0]
                
                check = {
                    'table': table_name,
                    'column': column,
                    'check': 'null_check',
                    'null_count': null_count,
                    'status': 'PASS' if null_count == 0 else 'FAILED',
                    'message': f'Found {null_count} null values' if null_count > 0 else 'No null values'
                }
                checks.append(check)
                
                if null_count > 0:
                    logger.warning(f"❌ Found {null_count} null values in {table_name}.{column}")
        
        return checks
    
    def check_data_freshness(self, table_name: str, date_column: str):
        """Check if data is fresh (most recent date is today or yesterday)"""
        with db.get_connection() as conn:
            query = f"""
            SELECT MAX({date_column}) as latest_date
            FROM {table_name}
            """
            result = pd.read_sql_query(query, conn)
            latest_date = result['latest_date'].iloc[0]
            
            if pd.isna(latest_date):
                return {
                    'table': table_name,
                    'check': 'freshness_check',
                    'status': 'FAILED',
                    'message': 'No data found',
                    'latest_date': None
                }
            
            days_diff = (datetime.now().date() - latest_date.date()).days
            
            status = 'PASS' if days_diff <= 2 else 'FAILED'
            message = f'Data is {days_diff} days old'
            
            if days_diff > 2:
                logger.warning(f"❌ Data in {table_name} is {days_diff} days old")
            
            return {
                'table': table_name,
                'check': 'freshness_check',
                'status': status,
                'message': message,
                'latest_date': latest_date,
                'days_old': days_diff
            }
    
    def check_value_ranges(self, table_name: str, column: str, min_val=None, max_val=None):
        """Check if column values are within expected range"""
        with db.get_connection() as conn:
            conditions = []
            if min_val is not None:
                conditions.append(f"{column} < {min_val}")
            if max_val is not None:
                conditions.append(f"{column} > {max_val}")
            
            if not conditions:
                return {
                    'table': table_name,
                    'check': 'range_check',
                    'status': 'SKIPPED',
                    'message': 'No range specified'
                }
            
            where_clause = " OR ".join(conditions)
            query = f"""
            SELECT COUNT(*) as outlier_count
            FROM {table_name}
            WHERE {where_clause}
            """
            
            result = pd.read_sql_query(query, conn)
            outlier_count = result['outlier_count'].iloc[0]
            
            status = 'PASS' if outlier_count == 0 else 'FAILED'
            message = f'Found {outlier_count} outliers' if outlier_count > 0 else 'No outliers'
            
            if outlier_count > 0:
                logger.warning(f"❌ Found {outlier_count} outliers in {table_name}.{column}")
            
            return {
                'table': table_name,
                'column': column,
                'check': 'range_check',
                'status': status,
                'message': message,
                'outlier_count': outlier_count,
                'min': min_val,
                'max': max_val
            }
    
    def check_referential_integrity(self, parent_table: str, child_table: str, fk_column: str):
        """Check referential integrity between tables"""
        with db.get_connection() as conn:
            query = f"""
            SELECT COUNT(*) as orphan_count
            FROM {child_table} c
            LEFT JOIN {parent_table} p ON c.{fk_column} = p.{fk_column.split('.')[-1]}
            WHERE p.{fk_column.split('.')[-1]} IS NULL
            """
            
            result = pd.read_sql_query(query, conn)
            orphan_count = result['orphan_count'].iloc[0]
            
            status = 'PASS' if orphan_count == 0 else 'FAILED'
            message = f'Found {orphan_count} orphan records' if orphan_count > 0 else 'No orphan records'
            
            if orphan_count > 0:
                logger.warning(f"❌ Found {orphan_count} orphan records in {child_table}")
            
            return {
                'parent_table': parent_table,
                'child_table': child_table,
                'fk_column': fk_column,
                'check': 'referential_integrity',
                'status': status,
                'message': message,
                'orphan_count': orphan_count
            }
    
    def run_all_checks(self, date_value: datetime = None):
        """Run all data quality checks"""
        logger.info("🔍 Running all data quality checks...")
        
        all_checks = []
        
        # Check nulls in all tables
        for table in ['users', 'products', 'orders', 'events']:
            all_checks.extend(self.check_nulls(table))
        
        # Check data freshness
        all_checks.append(self.check_data_freshness('orders', 'order_date'))
        all_checks.append(self.check_data_freshness('events', 'timestamp'))
        
        # Check value ranges
        all_checks.append(self.check_value_ranges('products', 'price', min_val=0))
        all_checks.append(self.check_value_ranges('orders', 'total_amount', min_val=0))
        
        # Check referential integrity
        all_checks.append(self.check_referential_integrity('users', 'orders', 'user_id'))
        all_checks.append(self.check_referential_integrity('products', 'order_items', 'product_id'))
        all_checks.append(self.check_referential_integrity('orders', 'order_items', 'order_id'))
        
        # Summary
        passed = sum(1 for check in all_checks if check.get('status') == 'PASS')
        failed = sum(1 for check in all_checks if check.get('status') == 'FAILED')
        skipped = sum(1 for check in all_checks if check.get('status') == 'SKIPPED')
        
        logger.info(f"📊 Data Quality Summary: {passed} PASS, {failed} FAILED, {skipped} SKIPPED")
        
        return all_checks

def run_daily_quality_checks(date_value: datetime):
    """Run daily quality checks (to be called from Airflow)"""
    checker = DataQualityChecker()
    return checker.run_all_checks(date_value)

# Test function
if __name__ == "__main__":
    checker = DataQualityChecker()
    checks = checker.run_all_checks()
    
    print("\n📋 Data Quality Check Results:")
    print("-" * 80)
    
    for check in checks:
        status_icon = "✅" if check['status'] == 'PASS' else "❌" if check['status'] == 'FAILED' else "⚠️"
        print(f"{status_icon} {check['table'] if 'table' in check else check.get('parent_table', 'N/A')}: {check.get('message', '')}")