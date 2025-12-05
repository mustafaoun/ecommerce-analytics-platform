-- src/database/powerbi_views.sql
-- Create optimized views for Power BI reporting

-- 1. Sales Summary View
DROP VIEW IF EXISTS sales_summary;
CREATE OR REPLACE VIEW sales_summary AS
SELECT 
    DATE_TRUNC('day', o.order_date) as order_date,
    DATE_TRUNC('week', o.order_date) as order_week,
    DATE_TRUNC('month', o.order_date) as order_month,
    DATE_TRUNC('quarter', o.order_date) as order_quarter,
    
    -- Dimensions
    u.user_id,
    u.country as user_country,
    u.city as user_city,
    u.acquisition_channel,
    DATE_TRUNC('month', u.signup_date) as user_cohort_month,
    
    p.product_id,
    p.name as product_name,
    p.category,
    p.subcategory,
    
    -- Measures
    COUNT(DISTINCT o.order_id) as order_count,
    SUM(o.total_amount) as total_revenue,
    SUM(oi.quantity) as total_quantity,
    SUM(oi.quantity * (oi.price_at_time - p.cost)) as total_profit,
    AVG(o.total_amount) as avg_order_value,
    
    -- Customer metrics
    COUNT(DISTINCT CASE WHEN DATE(o.order_date) = DATE(u.signup_date) THEN u.user_id END) as new_customers,
    COUNT(DISTINCT o.user_id) as active_customers
    
FROM orders o
JOIN users u ON o.user_id = u.user_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status = 'completed'
GROUP BY 
    DATE_TRUNC('day', o.order_date),
    DATE_TRUNC('week', o.order_date),
    DATE_TRUNC('month', o.order_date),
    DATE_TRUNC('quarter', o.order_date),
    u.user_id, u.country, u.city, u.acquisition_channel, DATE_TRUNC('month', u.signup_date),
    p.product_id, p.name, p.category, p.subcategory;

-- 2. Customer Lifetime Value View
DROP VIEW IF EXISTS customer_lifetime_value_view;
CREATE OR REPLACE VIEW customer_lifetime_value_view AS
WITH customer_stats AS (
    SELECT 
        u.user_id,
        u.email,
        u.country,
        u.city,
        u.signup_date,
        u.acquisition_channel,
        
        -- Order metrics
        COUNT(DISTINCT o.order_id) as total_orders,
        SUM(o.total_amount) as total_spent,
        MIN(o.order_date) as first_order_date,
        MAX(o.order_date) as last_order_date,
        
        -- Calculate days active
        EXTRACT(DAY FROM (MAX(o.order_date) - MIN(o.order_date))) as days_active,
        
        -- Calculate average days between orders
        CASE 
            WHEN COUNT(DISTINCT o.order_date) > 1 
            THEN EXTRACT(DAY FROM (MAX(o.order_date) - MIN(o.order_date))) / (COUNT(DISTINCT o.order_date) - 1)
            ELSE 0 
        END as avg_days_between_orders
        
    FROM users u
    LEFT JOIN orders o ON u.user_id = o.user_id
    WHERE o.status = 'completed' OR o.order_id IS NULL
    GROUP BY u.user_id, u.email, u.country, u.city, u.signup_date, u.acquisition_channel
),
customer_segments AS (
    SELECT 
        *,
        CASE 
            WHEN total_spent >= 1000 THEN 'VIP'
            WHEN total_spent >= 500 THEN 'Premium'
            WHEN total_spent >= 100 THEN 'Regular'
            WHEN total_spent > 0 THEN 'Casual'
            ELSE 'Inactive'
        END as customer_tier,
        
        CASE 
            WHEN last_order_date >= CURRENT_DATE - INTERVAL '30 days' THEN 'Active (< 30 days)'
            WHEN last_order_date >= CURRENT_DATE - INTERVAL '90 days' THEN 'Warm (30-90 days)'
            WHEN last_order_date >= CURRENT_DATE - INTERVAL '180 days' THEN 'Cold (90-180 days)'
            ELSE 'Dormant (> 180 days)'
        END as recency_segment
        
    FROM customer_stats
)
SELECT 
    *,
    CASE 
        WHEN total_spent > 0 THEN ROUND(total_spent / NULLIF(total_orders, 0), 2)
        ELSE 0 
    END as avg_order_value,
    
    CASE 
        WHEN total_orders > 0 THEN ROUND(total_spent / NULLIF(total_orders, 0), 2)
        ELSE 0 
    END as customer_lifetime_value
    
FROM customer_segments;

-- 3. Product Performance View
DROP VIEW IF EXISTS product_performance_view;
CREATE OR REPLACE VIEW product_performance_view AS
WITH product_stats AS (
    SELECT 
        p.product_id,
        p.name,
        p.category,
        p.subcategory,
        p.price,
        p.cost,
        
        -- Sales metrics
        COUNT(DISTINCT oi.order_id) as times_ordered,
        SUM(oi.quantity) as total_quantity_sold,
        SUM(oi.quantity * oi.price_at_time) as total_revenue,
        SUM(oi.quantity * (oi.price_at_time - p.cost)) as total_profit,
        
        -- Inventory metrics (simulated)
        CASE 
            WHEN SUM(oi.quantity) > 50 THEN 'High'
            WHEN SUM(oi.quantity) > 20 THEN 'Medium'
            ELSE 'Low'
        END as demand_level,
        
        -- Profit margin
        CASE 
            WHEN SUM(oi.quantity * oi.price_at_time) > 0 
            THEN ROUND((SUM(oi.quantity * (oi.price_at_time - p.cost)) / SUM(oi.quantity * oi.price_at_time)) * 100, 2)
            ELSE 0 
        END as profit_margin_percent
        
    FROM products p
    LEFT JOIN order_items oi ON p.product_id = oi.product_id
    LEFT JOIN orders o ON oi.order_id = o.order_id AND o.status = 'completed'
    GROUP BY p.product_id, p.name, p.category, p.subcategory, p.price, p.cost
),
ranked_products AS (
    SELECT 
        *,
        RANK() OVER (PARTITION BY category ORDER BY total_revenue DESC) as category_rank,
        RANK() OVER (ORDER BY total_revenue DESC) as overall_rank
    FROM product_stats
)
SELECT 
    *,
    CASE 
        WHEN category_rank <= 3 THEN 'Top 3 in Category'
        WHEN category_rank <= 10 THEN 'Top 10 in Category'
        ELSE 'Other'
    END as category_performance,
    
    CASE 
        WHEN overall_rank <= 10 THEN 'Top 10 Overall'
        WHEN overall_rank <= 50 THEN 'Top 50 Overall'
        ELSE 'Other'
    END as overall_performance
    
FROM ranked_products;

-- 4. Daily KPI View (for dashboard KPIs)
DROP VIEW IF EXISTS daily_kpi_view;
CREATE OR REPLACE VIEW daily_kpi_view AS
WITH daily_metrics AS (
    SELECT 
        DATE(o.order_date) as date,
        
        -- Revenue metrics
        SUM(o.total_amount) as daily_revenue,
        COUNT(DISTINCT o.order_id) as daily_orders,
        AVG(o.total_amount) as avg_order_value,
        
        -- Customer metrics
        COUNT(DISTINCT o.user_id) as daily_active_customers,
        COUNT(DISTINCT CASE WHEN DATE(u.signup_date) = DATE(o.order_date) THEN u.user_id END) as new_customers,
        
        -- Conversion metrics (simplified)
        COUNT(DISTINCT e.session_id) as daily_sessions
        
    FROM orders o
    JOIN users u ON o.user_id = u.user_id
    LEFT JOIN events e ON DATE(e.timestamp) = DATE(o.order_date)
    WHERE o.status = 'completed'
    GROUP BY DATE(o.order_date)
),
rolling_metrics AS (
    SELECT 
        *,
        AVG(daily_revenue) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as rolling_7d_revenue,
        AVG(daily_orders) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as rolling_7d_orders,
        
        -- Month-to-date
        SUM(daily_revenue) OVER (PARTITION BY DATE_TRUNC('month', date) ORDER BY date) as mtd_revenue,
        SUM(daily_orders) OVER (PARTITION BY DATE_TRUNC('month', date) ORDER BY date) as mtd_orders
        
    FROM daily_metrics
)
SELECT 
    *,
    ROUND(rolling_7d_revenue, 2) as rolling_7d_revenue_rounded,
    ROUND(rolling_7d_orders, 1) as rolling_7d_orders_rounded,
    
    -- Daily growth rates
    CASE 
        WHEN LAG(daily_revenue) OVER (ORDER BY date) > 0 
        THEN ROUND(((daily_revenue - LAG(daily_revenue) OVER (ORDER BY date)) / LAG(daily_revenue) OVER (ORDER BY date)) * 100, 2)
        ELSE NULL 
    END as revenue_growth_rate,
    
    -- Conversion rate (simplified)
    CASE 
        WHEN daily_sessions > 0 
        THEN ROUND((daily_orders * 100.0 / daily_sessions), 2)
        ELSE 0 
    END as conversion_rate
    
FROM rolling_metrics
ORDER BY date DESC;

-- 5. Geographic Performance View
DROP VIEW IF EXISTS geographic_performance_view;
CREATE OR REPLACE VIEW geographic_performance_view AS
SELECT 
    u.country,
    u.city,
    
    COUNT(DISTINCT u.user_id) as total_customers,
    COUNT(DISTINCT o.order_id) as total_orders,
    SUM(o.total_amount) as total_revenue,
    AVG(o.total_amount) as avg_order_value,
    
    -- Customer density
    ROUND(COUNT(DISTINCT u.user_id) * 1.0 / NULLIF(COUNT(DISTINCT u.city), 0), 2) as customers_per_city,
    
    -- Revenue per customer
    ROUND(SUM(o.total_amount) * 1.0 / NULLIF(COUNT(DISTINCT u.user_id), 0), 2) as revenue_per_customer
    
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id AND o.status = 'completed'
WHERE u.country IS NOT NULL
GROUP BY u.country, u.city
HAVING COUNT(DISTINCT u.user_id) > 0;

-- Create indexes for Power BI performance
CREATE INDEX IF NOT EXISTS idx_orders_order_date_status ON orders(order_date, status);
CREATE INDEX IF NOT EXISTS idx_users_country_signup ON users(country, signup_date);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);