import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys
import logging
from sqlalchemy import create_engine
import argparse
from typing import Optional, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ReportGenerator:
    """
    Generates various analytical reports for the e-commerce platform,
    fetching data from a PostgreSQL database and outputting HTML visualizations.
    """
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = create_engine(self.db_url)
        self.reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'reports')
        os.makedirs(self.reports_dir, exist_ok=True)
        self.start_date: Optional[str] = None
        self.end_date: Optional[str] = None

    def _execute_query(self, query: str) -> pd.DataFrame:
        """Executes a SQL query and returns the result as a DataFrame."""
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql_query(query, conn)
            return df
        except Exception as e:
            logging.error(f"Error executing SQL query: {e}")
            raise

    def _save_report(self, fig: go.Figure, filename_prefix: str) -> str:
        """Saves a Plotly figure as an HTML file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.html"
        filepath = os.path.join(self.reports_dir, filename)
        fig.write_html(filepath, full_html=True)
        return filepath

    def set_date_range(self, start_date: str, end_date: str):
        """Sets the reporting date range."""
        self.start_date = start_date
        self.end_date = end_date

    # --- Cohort Analysis ---

    def generate_cohort_analysis(self) -> str:
        """
        Generates a monthly retention cohort analysis heatmap.
        The analysis tracks user retention over 6 months from their sign-up month.
        """
        logging.info("👥 Generating cohort analysis...")

        # SQL query to fetch cohort data
        cohort_query = f"""
            WITH user_cohorts AS (
                SELECT
                    user_id,
                    -- FIX: The column 'created_at' does not exist in the 'users' table, causing a
                    -- psycopg2.errors.UndefinedColumn error. We are changing it to 'signup_date'.
                    -- **ACTION REQUIRED**: Please verify the correct column name for user registration
                    -- date in your 'users' table (e.g., 'signup_date', 'registration_date', 'joined_at').
                    DATE_TRUNC('month', signup_date) as cohort_month
                FROM users
            ),
            monthly_activity AS (
                SELECT
                    uc.cohort_month,
                    DATE_TRUNC('month', o.order_date) as activity_month,
                    COUNT(DISTINCT uc.user_id) as active_users
                FROM user_cohorts uc
                LEFT JOIN orders o ON uc.user_id = o.user_id
                -- Only consider orders that are completed and within a 6-month window of the cohort start
                AND o.status = 'completed'
                AND o.order_date >= uc.cohort_month
                AND o.order_date < uc.cohort_month + INTERVAL '6 months'
                GROUP BY 1, 2
            ),
            cohort_sizes AS (
                SELECT
                    cohort_month,
                    COUNT(DISTINCT user_id) as cohort_size
                FROM user_cohorts
                GROUP BY 1
            )
            SELECT
                ma.cohort_month,
                ma.activity_month,
                cs.cohort_size,
                ma.active_users,
                ROUND(ma.active_users * 100.0 / cs.cohort_size, 1) as retention_rate
            FROM monthly_activity ma
            JOIN cohort_sizes cs ON ma.cohort_month = cs.cohort_month
            WHERE ma.activity_month IS NOT NULL
            ORDER BY ma.cohort_month, ma.activity_month
        """

        try:
            cohort_df = pd.read_sql_query(cohort_query, self.engine)
        except Exception as e:
            logging.error(f"Failed to fetch cohort data. Please check the 'signup_date' column name in the 'users' table.")
            raise

        if cohort_df.empty:
            logging.warning("Cohort analysis skipped: No data found.")
            return ""

        # Calculate Period Number (Month Offset)
        cohort_df['cohort_period'] = (
            (cohort_df.activity_month.dt.year - cohort_df.cohort_month.dt.year) * 12 +
            (cohort_df.activity_month.dt.month - cohort_df.cohort_month.dt.month)
        )

        # Pivot the data for the heatmap
        cohort_pivot = cohort_df.pivot_table(
            index='cohort_month',
            columns='cohort_period',
            values='retention_rate'
        )

        # Format cohort_month for display
        cohort_pivot.index = cohort_pivot.index.strftime('%Y-%m')

        # Create the Plotly Heatmap
        fig = px.imshow(
            cohort_pivot,
            text_auto=True,
            aspect="auto",
            color_continuous_scale=px.colors.sequential.Plotly3,
            title=f"User Retention Cohort Analysis (Monthly)",
        )

        fig.update_xaxes(side="top", title='Retention Month (0 = Cohort Month)')
        fig.update_yaxes(title='Acquisition Cohort (Month)')

        # Add initial cohort size annotation
        cohort_sizes = cohort_df.drop_duplicates(subset=['cohort_month'])[['cohort_month', 'cohort_size']]
        cohort_size_map = cohort_sizes.set_index('cohort_month')['cohort_size'].to_dict()

        annotations = []
        for i, cohort_month in enumerate(cohort_pivot.index):
            size = cohort_size_map[datetime.strptime(cohort_month, '%Y-%m')]
            annotations.append(
                dict(
                    x=-0.5, y=i,
                    text=f"N={size}",
                    xref="x", yref="y",
                    showarrow=False,
                    font=dict(color="black", size=10),
                    xanchor='right',
                )
            )

        fig.update_layout(
            annotations=annotations,
            xaxis=dict(tickmode='array', tickvals=list(range(cohort_pivot.shape[1])), ticktext=[f'Month {i}' for i in range(cohort_pivot.shape[1])]),
            margin=dict(l=100, r=50, t=80, b=50),
            height=600
        )

        filepath = self._save_report(fig, "cohort_analysis")
        logging.info(f"✅ Cohort analysis generated: {filepath}")
        return filepath

    # --- Other Reports (Placeholder for context) ---

    def generate_executive_summary(self) -> str:
        """Generates the Executive Summary report."""
        # This function is assumed to be correct based on the traceback success
        # Placeholder implementation for completeness, though not the focus of the fix
        logging.info(f"📊 Generating executive summary for {self.start_date} to {self.end_date}...")
        
        # ... (Actual query execution and data processing would go here)
        
        # Create a dummy figure for demonstration
        fig = go.Figure()
        fig.add_trace(go.Bar(x=['Sales', 'Users', 'AOV'], y=[1000, 500, 50], name='Metrics'))
        fig.update_layout(
            title=f"Executive Summary ({self.start_date} to {self.end_date})",
            template="plotly_white"
        )

        filepath = self._save_report(fig, "executive_summary")
        logging.info(f"✅ Executive summary generated: {filepath}")
        return filepath

    def generate_product_performance(self) -> str:
        """Generates the Product Performance report."""
        logging.info("📦 Generating product performance report...")
        # ... (implementation)
        return "" # Placeholder

    def generate_all_reports(self) -> List[str]:
        """Generates all reports available."""
        logging.info("📄 Generating all reports...")
        if not self.start_date or not self.end_date:
            # Use a default range if not set, mirroring the user's initial run.
            self.set_date_range(
                (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'), 
                datetime.now().strftime('%Y-%m-%d')
            )
        
        reports = []
        
        # 1. Executive Summary
        try:
            reports.append(self.generate_executive_summary())
        except Exception as e:
            logging.error(f"Could not generate Executive Summary: {e}")

        # 2. Cohort Analysis (The problematic one)
        try:
            reports.append(self.generate_cohort_analysis())
        except Exception as e:
            logging.error(f"Could not generate Cohort Analysis: {e}")

        # 3. Product Performance
        try:
            reports.append(self.generate_product_performance())
        except Exception as e:
            logging.error(f"Could not generate Product Performance: {e}")

        return [r for r in reports if r]

def main():
    parser = argparse.ArgumentParser(description="E-commerce Analytics Report Generator")
    parser.add_argument("--db-url", type=str, default="postgresql://user:password@localhost:5432/ecommerce_db",
                        help="Database connection URL.")
    parser.add_argument("--start-date", type=str, default=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                        help="Start date for reports (YYYY-MM-DD).")
    parser.add_argument("--end-date", type=str, default=datetime.now().strftime('%Y-%m-%d'),
                        help="End date for reports (YYYY-MM-DD).")
    parser.add_argument("--all", action="store_true", help="Generate all reports.")

    args = parser.parse_args()

    # NOTE: The database URL should be securely configured, this is a placeholder.
    db_url_config = os.environ.get("DATABASE_URL", args.db_url)

    generator = ReportGenerator(db_url_config)
    generator.set_date_range(args.start_date, args.end_date)

    if args.all:
        generator.generate_all_reports()
    # Add other report-specific generation calls here if needed

if __name__ == "__main__":
    # Ensure the script runs if executed directly
    main()