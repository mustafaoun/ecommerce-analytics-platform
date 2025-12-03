# scripts/full_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analytics.forecasting import SalesForecaster
from src.analytics.kpi_calculator import KPICalculator

st.set_page_config(page_title="E-commerce Analytics Dashboard", layout="wide")

st.title("🚀 E-commerce Analytics Platform Dashboard")

# Sidebar for navigation
st.sidebar.title("Navigation")
section = st.sidebar.selectbox("Choose section", ["Overview", "Forecasting", "KPIs", "Channels & Inventory"])

calculator = KPICalculator()
forecaster = SalesForecaster()

if section == "Overview":
    st.header("📊 Key Metrics Overview")
    col1, col2, col3, col4 = st.columns(4)
    metrics = calculator.calculate_key_metrics()
    
    col1.metric("AOV", f"${metrics['AOV']:,.2f}")
    col2.metric("CLV", f"${metrics['CLV']:,.2f}")
    col3.metric("Retention Rate", f"{metrics['Retention Rate (%)']:.1f}%") 
    col4.metric("CAC", f"${metrics['CAC']:,.2f}")

    st.subheader("Daily Revenue Trend (Last 90 Days)")
    daily_df = calculator.get_daily_kpis()
    fig = px.line(daily_df, x='date', y='total_revenue', title="Daily Revenue")
    st.plotly_chart(fig, use_container_width=True)

elif section == "Forecasting":
    st.header("🔮 Sales Forecasting")
    with st.spinner('Training Prophet Model...'):
        forecaster.train_model()
    forecast = forecaster.forecast_future(30)
    metrics = forecaster.get_key_metrics()
    col1, col2 = st.columns(2)
    col1.metric("Next 7 Days Revenue", f"${metrics['next_7_days_revenue']:,.2f}")
    col2.metric("Next 30 Days Revenue", f"${metrics['next_30_days_revenue']:,.2f}")

    st.subheader("Forecast Plot")
    fig = go.Figure()
    hist_data = forecaster.load_historical_data()
    hist_len = len(hist_data)
    fig.add_trace(go.Scatter(x=forecast['ds'][:hist_len], y=forecast['yhat'][:hist_len], mode='lines', name='Historical', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Forecast', line=dict(color='red', dash='dash')))
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_upper'], fill=None, mode='lines', line_color='red', showlegend=False))
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_lower'], fill='tonexty', mode='lines', fillcolor='rgba(255,0,0,0.2)', line_color='red', name='Uncertainty'))
    fig.update_layout(title='Sales Forecast', xaxis_title='Date', yaxis_title='Daily Revenue ($)')
    st.plotly_chart(fig, use_container_width=True)

elif section == "KPIs":
    st.header("📈 Advanced KPIs")
    st.subheader("Customer Lifetime Value Distribution")
    ltv_df = calculator.get_customer_ltv()
    fig_hist = px.histogram(ltv_df, x='total_spent', nbins=20, title="CLV Distribution")
    st.plotly_chart(fig_hist, use_container_width=True)

    st.subheader("Retention Cohort Heatmap")
    cohort_df = calculator.calculate_retention_cohort()
    cohort_pivot = cohort_df.pivot_table(index='cohort_month', columns='period', values='retention_rate', aggfunc='mean').fillna(0) * 100
    fig_heat = px.imshow(cohort_pivot, title="Retention Rate % by Cohort & Period", color_continuous_scale='RdYlGn')
    st.plotly_chart(fig_heat, use_container_width=True)

elif section == "Channels & Inventory":
    st.header("📱 Channels ROI & Inventory Turnover")
    roi_df = calculator.calculate_channel_roi()
    st.subheader("Channel ROI")
    fig_roi = px.bar(roi_df, x='acquisition_channel', y='roi', title="ROI per Channel")
    st.plotly_chart(fig_roi, use_container_width=True)

    # Inventory Turnover is now expected to work after schema update
    turnover_df = calculator.calculate_inventory_turnover()
    st.subheader("Inventory Turnover by Category")
    fig_turn = px.bar(turnover_df, x='category', y='turnover_rate', title="Turnover Rate (times/year)")
    st.plotly_chart(fig_turn, use_container_width=True)


st.sidebar.markdown("---")
st.sidebar.info("Powered by Prophet, Plotly, and PostgreSQL")

if st.sidebar.button("Refresh Data"):
    st.rerun()