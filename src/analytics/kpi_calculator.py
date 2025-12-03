import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import logging
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class KPICalculator:
    def __init__(self):
        self.db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?sslmode=require"
        self.engine = create_engine(self.db_url)
    
    def get_daily_kpis(self):
        """Fetch daily KPIs from view"""
        query = "SELECT * FROM daily_kpis ORDER BY date DESC LIMIT 90;"
        df = pd.read_sql_query(query, self.engine)
        df['date'] = pd.to_datetime(df['date'])
        logger.info(f"Loaded {len(df)} daily KPIs")
        return df
    
    def get_customer_ltv(self):
        """Fetch customer lifetime value from view"""
        query = "SELECT * FROM customer_lifetime_value WHERE total_spent > 0 ORDER BY total_spent DESC LIMIT 500;"
        df = pd.read_sql_query(query, self.engine)
        df['signup_date'] = pd.to_datetime(df['signup_date'])
        if 'first_order_date' in df.columns:
            df['first_order_date'] = pd.to_datetime(df['first_order_date'])
        logger.info(f"Loaded {len(df)} customer LTV records")
        return df
    
    def calculate_retention_cohort(self, periods=12):
        """Calculate monthly retention cohort analysis"""
        cohort_query = """
        WITH user_cohorts AS (
            SELECT 
                user_id,
                DATE_TRUNC('month', signup_date) as cohort_month
            FROM users
        ),
        monthly_activity AS (
            SELECT 
                o.user_id,
                uc.cohort_month,
                DATE_TRUNC('month', o.order_date) as activity_month
            FROM orders o
            JOIN user_cohorts uc ON o.user_id = uc.user_id
            GROUP BY 1, 2, 3
        )
        SELECT 
            cohort_month,
            activity_month,
            COUNT(DISTINCT user_id) as retained_users
        FROM monthly_activity
        GROUP BY cohort_month, activity_month
        ORDER BY cohort_month, activity_month;
        """
        df = pd.read_sql_query(cohort_query, self.engine)
        df['cohort_month'] = pd.to_datetime(df['cohort_month'])
        df['activity_month'] = pd.to_datetime(df['activity_month'])
        
        # Remove timezone localization to ensure compatibility for subtraction
        df['cohort_month'] = df['cohort_month'].dt.tz_localize(None)
        df['activity_month'] = df['activity_month'].dt.tz_localize(None)
        
        # Calculate the month index (period) since signup
        df['period'] = (df['activity_month'] - df['cohort_month']).dt.days // 30 
        
        # Calculate initial cohort size for each month
        cohort_sizes = df[df['period'] == 0].groupby('cohort_month')['retained_users'].sum().rename('initial_size')
        df = df.merge(cohort_sizes, on='cohort_month')
        
        # Calculate retention rate
        df['retention_rate'] = df['retained_users'] / df['initial_size']
        logger.info(f"Calculated retention for {len(df)} cohort periods")
        return df

    def calculate_channel_roi(self):
        """Calculate ROI per acquisition channel"""
        query = """
        SELECT 
            u.acquisition_channel,
            COUNT(DISTINCT u.user_id) as users,
            COUNT(DISTINCT o.order_id) as orders,
            ROUND(SUM(o.total_amount), 2) as revenue,
            ROUND(SUM(o.total_amount) / NULLIF(COUNT(DISTINCT u.user_id), 0), 2) as revenue_per_user,
            ROUND((SUM(o.total_amount) / NULLIF(COUNT(DISTINCT u.user_id), 0)) / 10, 2) as roi
        FROM users u
        LEFT JOIN orders o ON u.user_id = o.user_id
        GROUP BY u.acquisition_channel
        ORDER BY revenue DESC;
        """
        df = pd.read_sql_query(query, self.engine)
        logger.info(f"Channel ROI: {len(df)} channels")
        return df

    def calculate_inventory_turnover(self):
        """
        Calculate inventory turnover rate.
        FIXED: Uses the new 'stock_quantity' column.
        """
        query = """
        SELECT 
            p.category,
            -- Calculate Average Inventory based on the current stock quantity
            AVG(p.stock_quantity) as avg_inventory, 
            -- Calculate Units Sold from order_items
            SUM(oi.quantity) as units_sold,
            -- Calculate Turnover Rate: Units Sold / Average Inventory
            ROUND(SUM(oi.quantity) / NULLIF(AVG(p.stock_quantity), 0), 2) as turnover_rate
        FROM products p
        LEFT JOIN order_items oi ON p.product_id = oi.product_id
        GROUP BY p.category
        ORDER BY turnover_rate DESC;
        """
        df = pd.read_sql_query(query, self.engine)
        logger.info(f"Inventory turnover: {len(df)} categories")
        return df
    
    def calculate_key_metrics(self):
        """
        Calculate core KPIs.
        FIXED: Robust error checking for None/NaN values.
        """
        
        # AOV from orders
        aov_query = "SELECT ROUND(AVG(total_amount), 2) as aov FROM orders;"
        aov_result = pd.read_sql_query(aov_query, self.engine)
        # Check if the result is valid or default to 0.00
        aov = aov_result.iloc[0, 0] if not aov_result.empty and aov_result.iloc[0, 0] is not None else 0.00
        
        # CAC (simple: marketing budget / new users – assume budget $10k/month)
        new_users_query = "SELECT COUNT(*) as new_users FROM users WHERE signup_date >= CURRENT_DATE - INTERVAL '30 days';"
        new_users = pd.read_sql_query(new_users_query, self.engine).iloc[0, 0]
        # CAC calculation already handles division by zero, but ensure the new_users count is valid.
        new_users = new_users if new_users is not None else 0
        cac = 10000 / new_users if new_users > 0 else 0.00
        
        # Retention Rate (Avg Month 1 Retention)
        retention_query = """
        WITH cohort_periods AS (
            SELECT 
                u.user_id,
                DATE_TRUNC('month', u.signup_date) as cohort_month,
                DATE_TRUNC('month', o.order_date) as activity_month
            FROM users u
            JOIN orders o ON u.user_id = o.user_id
            GROUP BY 1, 2, 3
        ),
        cohort_analysis AS (
            SELECT
                cohort_month,
                activity_month,
                (EXTRACT(YEAR FROM activity_month) - EXTRACT(YEAR FROM cohort_month)) * 12 +
                (EXTRACT(MONTH FROM activity_month) - EXTRACT(MONTH FROM cohort_month)) AS period
            FROM cohort_periods
            GROUP BY 1, 2
        ),
        cohort_metrics AS (
            SELECT
                ca.cohort_month,
                ca.period,
                COUNT(DISTINCT cp.user_id) AS retained_users,
                (SELECT COUNT(user_id) FROM users WHERE DATE_TRUNC('month', signup_date) = ca.cohort_month) AS initial_size
            FROM cohort_analysis ca
            JOIN cohort_periods cp ON ca.cohort_month = cp.cohort_month AND ca.activity_month = cp.activity_month
            GROUP BY 1, 2
        )
        SELECT
            AVG(CAST(retained_users AS NUMERIC) / initial_size * 100) as retention_rate_pct
        FROM cohort_metrics
        WHERE period = 1 AND initial_size > 0;
        """
        result = pd.read_sql_query(retention_query, self.engine)
        # Check if the result is valid or default to 0.00
        retention = result.iloc[0, 0] if result.shape[0] > 0 and result.iloc[0, 0] is not None else 0.00
        
        # CLV (avg total_spent)
        clv_query = "SELECT ROUND(AVG(total_spent), 2) as clv FROM customer_lifetime_value WHERE total_spent > 0;"
        clv_result = pd.read_sql_query(clv_query, self.engine)
        # Check if the result is valid or default to 0.00
        clv = clv_result.iloc[0, 0] if not clv_result.empty and clv_result.iloc[0, 0] is not None else 0.00
        
        metrics = {
            'AOV': aov,
            'CAC': cac,
            'Retention Rate (%)': retention, 
            'CLV': clv
        }
        logger.info("Calculated key metrics")
        return metrics
    
    def create_kpi_dashboard(self):
        """Create interactive Plotly dashboard for KPIs"""
        # Get data
        daily_df = self.get_daily_kpis()
        ltv_df = self.get_customer_ltv()
        cohort_df = self.calculate_retention_cohort()
        metrics = self.calculate_key_metrics()
        
        # Run turnover calculation here, it should work after schema update
        turnover_df = self.calculate_inventory_turnover()
        
        # Subplots dashboard layout
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Daily Revenue Trend (Last 90 Days)', 'Retention Cohort Heatmap', 'CLV Distribution', 'Key Metrics'),
            specs=[[{"type": "scatter"}, {"type": "heatmap"}],
                   [{"type": "histogram"}, {"type": "table"}]]
        )
        
        # 1. Daily Revenue
        fig.add_trace(
            go.Scatter(x=daily_df['date'], y=daily_df['total_revenue'], mode='lines', name='Revenue'),
            row=1, col=1
        )
        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_yaxes(title_text="Revenue ($)", row=1, col=1)
        
        # 2. Retention Heatmap (pivot for cohort)
        cohort_pivot = cohort_df.pivot_table(index='cohort_month', columns='period', values='retention_rate', aggfunc='mean').fillna(0) * 100
        cohort_labels = [dt.strftime('%Y-%m') for dt in cohort_pivot.index]
        
        fig.add_trace(
            go.Heatmap(z=cohort_pivot.values, 
                       x=cohort_pivot.columns, 
                       y=cohort_labels, 
                       colorscale='RdYlGn',
                       text=cohort_pivot.apply(lambda x: [f'{y:.1f}%' for y in x], axis=1).values,
                       hoverongaps=False,
                       showscale=True,
                       colorbar=dict(title="Retention %")
                      ),
            row=1, col=2
        )
        fig.update_xaxes(title_text="Months Since Signup (Period)", row=1, col=2)
        fig.update_yaxes(title_text="Cohort Month", row=1, col=2)
        
        # 3. CLV Histogram
        fig.add_trace(
            go.Histogram(x=ltv_df['total_spent'], nbinsx=20, name='CLV Distribution', marker_color='#4682B4'),
            row=2, col=1
        )
        fig.update_xaxes(title_text="Total Spent (CLV)", row=2, col=1)
        fig.update_yaxes(title_text="Number of Customers", row=2, col=1)
        
        # 4. Key Metrics Table
        metrics_df = pd.DataFrame(list(metrics.items()), columns=['Metric', 'Value'])
        metrics_df['Value'] = metrics_df.apply(lambda row: f"${row['Value']:,.2f}" if 'CLV' in row['Metric'] or 'AOV' in row['Metric'] or 'CAC' in row['Metric'] else f"{row['Value']:,.2f}%", axis=1)
        
        fig.add_trace(
            go.Table(header=dict(values=['Metric', 'Value']),
                     cells=dict(values=[metrics_df['Metric'], metrics_df['Value']])),
            row=2, col=2
        )
        
        fig.update_layout(height=800, 
                          title_text="E-commerce KPIs Dashboard",
                          showlegend=False)
        fig.show()
        logger.info("KPI dashboard displayed")
        return fig

if __name__ == "__main__":
    calculator = KPICalculator()
    metrics = calculator.calculate_key_metrics()
    print("\n📊 Key Metrics:")
    print("=" * 25)
    for k, v in metrics.items():
        print(f"  {k}: {v:,.2f}{'%' if '%' in k else ''}")
        
    roi_df = calculator.calculate_channel_roi()
    turnover_df = calculator.calculate_inventory_turnover()
    
    print("\n📊 Channel ROI:")
    print(roi_df[['acquisition_channel', 'revenue_per_user', 'roi']].to_string(index=False))
    
    print("\n📊 Inventory Turnover:")
    print(turnover_df[['category', 'units_sold', 'avg_inventory', 'turnover_rate']].to_string(index=False))
    
    calculator.create_kpi_dashboard()