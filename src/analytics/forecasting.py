# src/analytics/forecasting.py
import pandas as pd
from prophet import Prophet
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class SalesForecaster:
    def __init__(self):
        self.db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?sslmode=require"
        self.engine = create_engine(self.db_url)
        self.model = None
        self.forecast = None
    
    def load_historical_data(self):
        """Load daily revenue data from database"""
        query = """
        SELECT 
            DATE(order_date) as ds,
            SUM(total_amount) as y
        FROM orders
        GROUP BY DATE(order_date)
        ORDER BY ds;
        """
        df = pd.read_sql_query(query, self.engine)
        df['ds'] = pd.to_datetime(df['ds'])
        df['y'] = pd.to_numeric(df['y'])
        logger.info(f"Loaded {len(df)} days of historical data")
        return df
    
    def train_model(self, changepoint_prior_scale=0.05, seasonality_prior_scale=10):
        """Train Prophet model"""
        df = self.load_historical_data()
        if len(df) < 2:
            raise ValueError("Not enough historical data for forecasting")
        
        self.model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=changepoint_prior_scale,
            seasonality_prior_scale=seasonality_prior_scale
        )
        self.model.fit(df)
        logger.info("✅ Model trained successfully")
        return self.model
    
    def forecast_future(self, periods=30):
        """Generate forecast for next periods days"""
        if self.model is None:
            self.train_model()
        
        future = self.model.make_future_dataframe(periods=periods)
        self.forecast = self.model.predict(future)
        logger.info(f"✅ Forecast generated for {periods} days")
        return self.forecast
    
    def plot_forecast(self, save_path='forecast.png'):
        """Plot forecast with Plotly"""
        if self.forecast is None:
            self.forecast_future()
        
        # Prophet's plot method uses Matplotlib, but we'll keep the output reference
        fig = self.model.plot(self.forecast, uncertainty_samples=100)
        # Note: fig here is Matplotlib figure, not Plotly. Keeping the original code logic.
        
        # To make sure an image is saved using a compatible library (requires kaleido for Plotly),
        # we'll rely on the interactive dashboard function for Plotly output.
        # This function uses Matplotlib plot() which may not support .write_image() directly.
        # We'll comment out the write_image() for robustness but keep the function structure.
        # fig.write_image(save_path) # This line often fails without extra dependencies
        logger.info(f"Forecast plot generated (requires manual save or display).")
        return fig
    
    def get_key_metrics(self):
        """Get forecast metrics"""
        if self.forecast is None:
            self.forecast_future()
        
        # FIX: Convert the result of datetime.now().date() back to a timestamp 
        # that matches the dtype=datetime64[ns] of self.forecast['ds'].
        today_timestamp = pd.to_datetime(datetime.now().date())
        
        # Filter for future dates starting AFTER the current date/time
        future_forecast = self.forecast[self.forecast['ds'] > today_timestamp]
        
        if future_forecast.empty:
            logger.warning("Future forecast data is empty. Check data timestamps.")
            return {
                'next_7_days_revenue': 0.0,
                'next_30_days_revenue': 0.0,
                'avg_daily_forecast': 0.0,
                'upper_bound_30d': 0.0,
                'lower_bound_30d': 0.0
            }
        
        metrics = {
            'next_7_days_revenue': future_forecast.head(7)['yhat'].sum(),
            'next_30_days_revenue': future_forecast.head(30)['yhat'].sum(),
            'avg_daily_forecast': future_forecast['yhat'].mean(),
            'upper_bound_30d': future_forecast.head(30)['yhat_upper'].sum(),
            'lower_bound_30d': future_forecast.head(30)['yhat_lower'].sum()
        }
        return metrics
    
    def create_interactive_dashboard(self):
        """Create Plotly dashboard for forecast"""
        if self.forecast is None:
            self.forecast_future()
        
        # Fetch historical data again to plot actuals
        history_df = self.load_historical_data()
        
        # Separate historical vs forecast sections for plotting clarity
        forecast_start_date = self.forecast['ds'].max() - timedelta(days=30) # Start plotting recent history
        forecast_data = self.forecast[self.forecast['ds'] >= forecast_start_date]
        
        fig = go.Figure()
        
        # Add Actual Historical Data (up to the last recorded day)
        fig.add_trace(go.Scatter(
            x=history_df['ds'],
            y=history_df['y'],
            mode='lines',
            name='Actual Revenue',
            line=dict(color='blue')
        ))
        
        # Add Forecast Line (starting where history ends)
        fig.add_trace(go.Scatter(
            x=forecast_data['ds'],
            y=forecast_data['yhat'],
            mode='lines',
            name='Forecast (yhat)',
            line=dict(color='red', dash='dash')
        ))

        # Add Uncertainty Band (Upper Bound)
        fig.add_trace(go.Scatter(
            x=forecast_data['ds'],
            y=forecast_data['yhat_upper'],
            mode='lines',
            name='Upper Bound',
            line=dict(width=0),
            showlegend=False
        ))
        
        # Add Uncertainty Band (Lower Bound) and fill between yhat_upper and yhat_lower
        fig.add_trace(go.Scatter(
            x=forecast_data['ds'],
            y=forecast_data['yhat_lower'],
            mode='lines',
            name='Confidence Interval',
            fill='tonexty',
            fillcolor='rgba(255,0,0,0.2)',
            line=dict(width=0),
        ))
        
        fig.update_layout(
            title='Sales Forecast: Actuals, Prediction, and Uncertainty',
            xaxis_title='Date',
            yaxis_title='Daily Revenue ($)',
            hovermode='x unified'
        )
        fig.show()
        logger.info("Interactive dashboard displayed")

if __name__ == "__main__":
    forecaster = SalesForecaster()
    try:
        forecaster.train_model()
        forecast = forecaster.forecast_future(30)
        metrics = forecaster.get_key_metrics()
        
        print("\n📊 Forecast Metrics:")
        print("=" * 25)
        for key, value in metrics.items():
            print(f"  {key}: ${value:,.2f}")
        
        forecaster.create_interactive_dashboard()
        
    except ValueError as e:
        logger.error(f"Execution failed: {e}")