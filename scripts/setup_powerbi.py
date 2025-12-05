import os
from pathlib import Path
from dotenv import load_dotenv

def generate_powerbi_connection():
    """Generate Power BI connection configuration"""
    
    print("🔗 Generating Power BI connection files...")
    
    # Load environment variables
    load_dotenv()
    
    # Create pbix_template directory
    template_dir = Path("powerbi")
    template_dir.mkdir(exist_ok=True)
    
    # 1. Create connection string file
    connection_string = f"Server={os.getenv('DB_HOST')};Port={os.getenv('DB_PORT')};Database={os.getenv('DB_NAME')};User Id={os.getenv('DB_USER')};Password={os.getenv('DB_PASSWORD')};"
    
    # Use utf-8 for file writing to ensure robustness across OS environments
    # and properly handle special characters/emojis.
    with open(template_dir / "connection_string.txt", "w", encoding="utf-8") as f:
        f.write(connection_string)
    
    # 2. Create Power Query M script for advanced transformations
    # NOTE on escaping: All literal curly braces in the M script must be doubled
    # (e.g., {{ becomes {) to prevent Python's .format() from trying to substitute them.
    # The Power Query M syntax for the column type transformation is:
    # {{{"Profit Margin", Percentage.Type}}}
    # This requires 4 opening and 4 closing braces in the Python format string.
    m_script = """
    let
        Source = PostgreSQL.Database("{server}", "{database}", [CreateNavigationProperties=false]),
        
        // Get sales summary
        sales_summary = Source{{[Schema="public", Item="sales_summary"]}}[Data],
        
        // Get customer lifetime value
        customer_lifetime = Source{{[Schema="public", Item="customer_lifetime_value_view"]}}[Data],
        
        // Get product performance
        product_performance = Source{{[Schema="public", Item="product_performance_view"]}}[Data],
        
        // Get daily KPIs
        daily_kpis = Source{{[Schema="public", Item="daily_kpi_view"]}}[Data],
        
        // Get geographic data
        geographic_data = Source{{[Schema="public", Item="geographic_performance_view"]}}[Data],
        
        // Create a combined fact table
        combined_fact = Table.Combine({{sales_summary, product_performance}}),
        
        // Add calculated columns
        #"Added Custom" = Table.AddColumn(combined_fact, "Profit Margin", each [total_profit] / [total_revenue]),
        // FIX: Escaping the literal M list braces for Python formatter:
        #"Changed Type" = Table.TransformColumnTypes(#"Added Custom",{{{{ "Profit Margin", Percentage.Type }}}} )
    in
        #"Changed Type"
    """.format(
        server=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME')
    )
    
    with open(template_dir / "power_query_m_script.txt", "w", encoding="utf-8") as f:
        f.write(m_script)
    
    # 3. Create DAX measures template
    dax_measures = """
    -- 📊 KEY DAX MEASURES FOR E-COMMERCE DASHBOARD
    -- =============================================

    -- 1. REVENUE METRICS
    Total Revenue = SUM(sales_summary[total_revenue])
    YTD Revenue = TOTALYTD([Total Revenue], 'Date'[Date])
    MTD Revenue = TOTALMTD([Total Revenue], 'Date'[Date])
    QTD Revenue = TOTALQTD([Total Revenue], 'Date'[Date])
    
    Avg Order Value = AVERAGE(sales_summary[avg_order_value])
    Revenue Growth % = 
        VAR PreviousRevenue = CALCULATE([Total Revenue], PREVIOUSMONTH('Date'[Date]))
        RETURN DIVIDE([Total Revenue] - PreviousRevenue, PreviousRevenue)
    
    -- 2. ORDER METRICS
    Total Orders = COUNTROWS(sales_summary)
    Order Growth % = 
        VAR PreviousOrders = CALCULATE([Total Orders], PREVIOUSMONTH('Date'[Date]))
        RETURN DIVIDE([Total Orders] - PreviousOrders, PreviousOrders)
    
    -- 3. CUSTOMER METRICS
    Total Customers = DISTINCTCOUNT(sales_summary[user_id])
    New Customers = SUM(sales_summary[new_customers])
    Active Customers = DISTINCTCOUNT(sales_summary[user_id])
    
    Customer Retention Rate = 
        VAR CurrentMonthCustomers = CALCULATE([Active Customers], DATEADD('Date'[Date], -1, MONTH))
        VAR PreviousMonthCustomers = CALCULATE([Active Customers], DATEADD('Date'[Date], -2, MONTH))
        RETURN DIVIDE(CurrentMonthCustomers, PreviousMonthCustomers)
    
    Customer Lifetime Value = AVERAGE(customer_lifetime_value_view[customer_lifetime_value])
    
    -- 4. PRODUCT METRICS
    Top Product Revenue = MAXX(ALL(product_performance_view), [total_revenue])
    Avg Profit Margin = AVERAGE(product_performance_view[profit_margin_percent])
    
    -- 5. GEOGRAPHIC METRICS
    Revenue per Country = SUM(geographic_performance_view[total_revenue])
    Customers per Country = DISTINCTCOUNT(geographic_performance_view[country])
    
    -- 6. TIME INTELLIGENCE
    Revenue Last Month = CALCULATE([Total Revenue], DATEADD('Date'[Date], -1, MONTH))
    Revenue Same Month Last Year = CALCULATE([Total Revenue], SAMEPERIODLASTYEAR('Date'[Date]))
    
    -- 7. KPI STATUS INDICATORS
    Revenue Target = 100000  -- Example target
    Revenue vs Target % = DIVIDE([Total Revenue], [Revenue Target])
    
    KPI Status = 
        SWITCH(TRUE(),
            [Revenue vs Target %] >= 1.1, "✅ Exceeding Target",
            [Revenue vs Target %] >= 1.0, "✅ Meeting Target",
            [Revenue vs Target %] >= 0.9, "⚠️ Slightly Below",
            "❌ Below Target"
        )
    """
    
    # FIX: Explicitly specify UTF-8 encoding to handle emojis (like 📊, ✅, ⚠️, ❌)
    with open(template_dir / "dax_measures.txt", "w", encoding="utf-8") as f:
        f.write(dax_measures)
    
    # 4. Create dashboard wireframe
    wireframe = """
    📱 POWER BI DASHBOARD WIREFRAME
    ================================
    
    PAGE 1: EXECUTIVE SUMMARY
    --------------------------
    [Header]
    - Logo
    - Date range slicer
    - KPI status indicators
    
    [KPI Cards - Top Row]
    Card 1: Total Revenue (with trend arrow)
    Card 2: Total Orders
    Card 3: Active Customers
    Card 4: Avg Order Value
    Card 5: Conversion Rate
    
    [Main Visualizations - Middle Section]
    Left: Revenue Trend (Line chart - Daily, Weekly, Monthly toggle)
    Middle: Revenue by Category (Donut chart)
    Right: Top 10 Products (Horizontal bar chart)
    
    [Bottom Section]
    Left: Geographic Revenue Map
    Right: Daily Revenue vs Target (Combo chart)
    
    PAGE 2: CUSTOMER ANALYTICS
    --------------------------
    [Customer Segmentation]
    - Customer Tier Distribution (Pie chart)
    - Recency Segment Analysis (Bar chart)
    - Customer Lifetime Value Distribution (Histogram)
    
    [Cohort Analysis]
    - Retention Matrix (Heatmap)
    - Cohort Revenue Over Time (Line chart)
    
    [Customer Journey]
    - Acquisition Channel Performance (Funnel chart)
    - Customer Geographic Distribution (Map)
    
    PAGE 3: PRODUCT ANALYTICS
    -------------------------
    [Product Performance]
    - Product Category Performance (Tree map)
    - Top/Bottom 10 Products (Bar charts)
    - Product Profit Margin Analysis (Scatter plot)
    
    [Inventory & Demand]
    - Stock Levels vs Sales (Combo chart)
    - Product Demand Forecasting (Line chart with forecast)
    - Seasonality Analysis (Decomposition tree)
    
    PAGE 4: MARKETING & SALES
    -------------------------
    [Marketing Performance]
    - Acquisition Channel ROI (Bar chart)
    - Campaign Performance (Matrix)
    - Customer Acquisition Cost by Channel (Waterfall)
    
    [Sales Funnel]
    - Conversion Funnel (Funnel chart)
    - Time to Purchase Analysis (Histogram)
    - Cart Abandonment Rate (Gauge)
    
    PAGE 5: GEOGRAPHIC ANALYTICS
    ----------------------------
    [Interactive Map]
    - Revenue Heat Map by Country/City
    - Customer Density Map
    - Avg Order Value by Region
    
    [Regional Performance]
    - Top Performing Regions (Bar chart)
    - Regional Growth Rates (Line chart)
    - Market Penetration Analysis (Scatter plot)
    
    PAGE 6: FORECASTING & PREDICTIVE
    --------------------------------
    [Demand Forecasting]
    - 30-Day Sales Forecast (Line chart with confidence interval)
    - Product Demand Predictions (Matrix)
    
    [Predictive Analytics]
    - Customer Churn Prediction (Gauge)
    - Next Best Product Recommendations (Card)
    - Customer Lifetime Value Prediction (Scatter plot)
    """
    
    with open(template_dir / "dashboard_wireframe.txt", "w", encoding="utf-8") as f:
        f.write(wireframe)
    
    # 5. Create step-by-step guide
    guide = """
    🚀 POWER BI SETUP GUIDE
    ======================
    
    STEP 1: CONNECT TO DATABASE
    ----------------------------
    1. Open Power BI Desktop
    2. Click "Get Data" -> "More..." -> "Database" -> "PostgreSQL database"
    3. Enter connection details:
        Server: aws-1-eu-west-1.pooler.supabase.com
        Database: postgres
        Username: postgres.uquruuixtmkpgivbtcjx
        Password: 5tF?36UXz$gFzb6
    4. Click "Connect"
    
    STEP 2: LOAD DATA TABLES
    ------------------------
    1. Select these tables:
        - sales_summary (VIEW)
        - customer_lifetime_value_view (VIEW)
        - product_performance_view (VIEW)
        - daily_kpi_view (VIEW)
        - geographic_performance_view (VIEW)
    2. Click "Load"
    
    STEP 3: CREATE DATA MODEL
    -------------------------
    1. Go to "Model" view
    2. Create relationships:
        - sales_summary[product_id] -> product_performance_view[product_id]
        - sales_summary[user_id] -> customer_lifetime_value_view[user_id]
    3. Mark 'Date' table:
        - Create Date table using:
          Date = CALENDAR(MIN(sales_summary[order_date]), MAX(sales_summary[order_date]))
        - Mark as Date table: Right-click -> Mark as date table
    
    STEP 4: CREATE DAX MEASURES
    ---------------------------
    1. Copy DAX measures from dax_measures.txt
    2. Paste into Power BI measures pane
    
    STEP 5: BUILD DASHBOARD PAGES
    -----------------------------
    1. Follow wireframe in dashboard_wireframe.txt
    2. Use visualizations from "Visualizations" pane
    3. Apply theme: View -> Themes -> Import theme -> Use included theme.json
    
    STEP 6: PUBLISH TO POWER BI SERVICE
    -----------------------------------
    1. File -> Publish -> Select workspace
    2. Set up scheduled refresh:
        - Power BI Service -> Dataset -> Settings
        - Configure data source credentials
        - Set refresh schedule (Daily at 6 AM)
    
    TIPS FOR PERFORMANCE:
    --------------------
    1. Use import mode (not DirectQuery) for better performance
    2. Aggregate data at database level before loading
    3. Use calculated columns sparingly
    4. Use DAX measures for calculations
    5. Hide unused columns from report view
    
    TROUBLESHOOTING:
    ----------------
    1. Connection failed: Check firewall settings, allow your IP in AWS RDS security group
    2. Slow performance: Create indexes, use materialized views
    3. Memory issues: Reduce data volume, use aggregation tables
    
    NEXT STEPS:
    -----------
    1. Add bookmarks for different views
    2. Create mobile-optimized layout
    3. Set up data alerts for KPIs
    4. Share with stakeholders
    """
    
    with open(template_dir / "setup_guide.txt", "w", encoding="utf-8") as f:
        f.write(guide)
    
    print(f"✅ Power BI files created in {template_dir}/")
    print("\n📋 Files created:")
    print("  • connection_string.txt - Database connection string")
    print("  • power_query_m_script.txt - Advanced transformations")
    print("  • dax_measures.txt - Key DAX measures")
    print("  • dashboard_wireframe.txt - Dashboard design")
    print("  • setup_guide.txt - Step-by-step instructions")

if __name__ == "__main__":
    generate_powerbi_connection()