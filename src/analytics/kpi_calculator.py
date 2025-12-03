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
        # Database connection setup
        self.db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?sslmode=require"
        self.engine = create_engine(self.db_url)
    
    def get_daily_kpis(self):
        """Fetch daily KPIs from view (last 90 days)"""
        query = "SELECT * FROM daily_kpis ORDER BY date DESC LIMIT 90;"
        df = pd.read_sql_query(query, self.engine)
        df['date'] = pd.to_datetime(df['date'])
        logger.info(f"Loaded {len(df)} daily KPIs")
        return df
    
    def get_customer_ltv(self):
        """Fetch customer lifetime value from view (top spenders)"""
        query = "SELECT * FROM customer_lifetime_value WHERE total_spent > 0 ORDER BY total_spent DESC LIMIT 500;"
        df = pd.read_sql_query(query, self.engine)
        df['signup_date'] = pd.to_datetime(df['signup_date'])
        if 'first_order_date' in df.columns:
            df['first_order_date'] = pd.to_datetime(df['first_order_date'])
        logger.info(f"Loaded {len(df)} customer LTV records")
        return df
    
    def calculate_retention_cohort(self, periods=12):
        """Calculate monthly retention cohort analysis"""
        # SQL query to get cohort and activity months for all users
        cohort_query = """
        WITH user_cohorts AS (
            SELECT 
                user_id,
                DATE_TRUNC('month', signup_date) as cohort_month,
                acquisition_channel
            FROM users
        ),
        monthly_activity AS (
            SELECT 
                uc.user_id,
                uc.cohort_month,
                uc.acquisition_channel,
                DATE_TRUNC('month', o.order_date) as activity_month,
                COUNT(DISTINCT o.order_id) as orders
            FROM user_cohorts uc
            LEFT JOIN orders o ON uc.user_id = o.user_id
            GROUP BY 1, 2, 3, 4
        )
        SELECT 
            cohort_month,
            activity_month,
            acquisition_channel,
            COUNT(DISTINCT user_id) as active_users,
            COUNT(DISTINCT CASE WHEN orders > 0 THEN user_id END) as retained_users
        FROM monthly_activity
        GROUP BY cohort_month, activity_month, acquisition_channel
        ORDER BY cohort_month, activity_month;
        """
        df = pd.read_sql_query(cohort_query, self.engine)
        
        df['cohort_month'] = pd.to_datetime(df['cohort_month'])
        df['activity_month'] = pd.to_datetime(df['activity_month'])
        
        # FIX: Remove timezone localization (tz_localize(None)) to ensure both datetime 
        # columns are timezone-naive before subtraction, resolving the TypeError.
        df['cohort_month'] = df['cohort_month'].dt.tz_localize(None)
        df['activity_month'] = df['activity_month'].dt.tz_localize(None)
        
        # Calculate the month index (period) since signup
        df['period'] = (df['activity_month'] - df['cohort_month']).dt.days // 30  # Approximate months
        
        # Calculate retention rate
        df['retention_rate'] = df['retained_users'] / df['active_users']
        logger.info(f"Calculated retention for {len(df)} cohort periods")
        return df
    
    def calculate_key_metrics(self):
        """Calculate core KPIs: AOV, CAC, Retention Rate, CLV"""
        # 1. AOV (Average Order Value)
        aov_query = "SELECT ROUND(AVG(total_amount), 2) as aov FROM orders;"
        aov = pd.read_sql_query(aov_query, self.engine).iloc[0, 0]
        
        # 2. CAC (Cost to Acquire Customer) - Assumed marketing budget $10k/month
        new_users_query = "SELECT COUNT(*) as new_users FROM users WHERE signup_date >= CURRENT_DATE - INTERVAL '30 days';"
        new_users = pd.read_sql_query(new_users_query, self.engine).iloc[0, 0]
        cac = 10000 / new_users if new_users > 0 else 0
        
        # 3. Retention Rate (monthly) - Simplified calculation
        retention_query = """
        WITH monthly_cohorts AS (
            SELECT 
                DATE_TRUNC('month', signup_date) as cohort,
                COUNT(*) as cohort_size
            FROM users
            GROUP BY cohort
        ),
        monthly_active AS (
            SELECT 
                DATE_TRUNC('month', o.order_date) as month,
                COUNT(DISTINCT o.user_id) as active
            FROM orders o
            GROUP BY month
        )
        SELECT 
            AVG(CAST(ma.active AS NUMERIC) / mc.cohort_size * 100) as retention_rate_pct
        FROM monthly_cohorts mc
        JOIN monthly_active ma ON ma.month = mc.cohort;
        """
        result = pd.read_sql_query(retention_query, self.engine)
        retention = result.iloc[0, 0] if result.shape[0] > 0 and result.iloc[0, 0] is not None else 0
        
        # 4. CLV (Customer Lifetime Value) - Average total spend
        clv_query = "SELECT ROUND(AVG(total_spent), 2) as clv FROM customer_lifetime_value WHERE total_spent > 0;"
        clv = pd.read_sql_query(clv_query, self.engine).iloc[0, 0]
        
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
        # We pivot the data to create the matrix for the heatmap
        cohort_pivot = cohort_df.pivot_table(index='cohort_month', columns='period', values='retention_rate', aggfunc='mean').fillna(0) * 100
        
        # Format the index for better labels
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
    calculator.create_kpi_dashboard()