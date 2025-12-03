
-- Sample SQL Queries for E-commerce Analysis
-- ===========================================

-- 1. Monthly Revenue Trend
SELECT 
    DATE_TRUNC('month', order_date) as month,
    COUNT(DISTINCT order_id) as orders,
    ROUND(SUM(total_amount), 2) as revenue,
    ROUND(AVG(total_amount), 2) as avg_order_value
FROM orders
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month DESC;

-- 2. Customer Retention (Cohort Analysis)
WITH user_cohorts AS (
    SELECT 
        user_id,
        DATE_TRUNC('month', signup_date) as cohort_month
    FROM users
),
monthly_orders AS (
    SELECT 
        u.user_id,
        u.cohort_month,
        DATE_TRUNC('month', o.order_date) as order_month,
        COUNT(DISTINCT o.order_id) as orders
    FROM user_cohorts u
    LEFT JOIN orders o ON u.user_id = o.user_id
    GROUP BY 1, 2, 3
)
SELECT 
    cohort_month,
    order_month,
    COUNT(DISTINCT user_id) as active_users
FROM monthly_orders
GROUP BY cohort_month, order_month
ORDER BY cohort_month, order_month;

-- 3. Product Category Performance
SELECT 
    p.category,
    COUNT(DISTINCT oi.order_id) as orders,
    SUM(oi.quantity) as units_sold,
    ROUND(SUM(oi.quantity * oi.price_at_time), 2) as revenue,
    ROUND(SUM(oi.quantity * (oi.price_at_time - p.cost)), 2) as profit
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.category
ORDER BY revenue DESC;

-- 4. Customer Lifetime Value
SELECT 
    u.user_id,
    u.email,
    u.signup_date,
    COUNT(DISTINCT o.order_id) as total_orders,
    ROUND(SUM(o.total_amount), 2) as total_spent,
    ROUND(AVG(o.total_amount), 2) as avg_order_value,
    MIN(o.order_date) as first_order,
    MAX(o.order_date) as last_order
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.email, u.signup_date
ORDER BY total_spent DESC NULLS LAST;

-- 5. Hourly Sales Distribution
SELECT 
    EXTRACT(HOUR FROM order_date) as hour_of_day,
    COUNT(*) as orders,
    ROUND(SUM(total_amount), 2) as revenue
FROM orders
GROUP BY EXTRACT(HOUR FROM order_date)
ORDER BY hour_of_day;
