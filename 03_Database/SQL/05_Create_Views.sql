-- ============================================================================
-- Enterprise Retail Decision Intelligence Platform
-- Script 05: Create Analytics Views (Business KPIs & RFM metrics)
-- ============================================================================

-- Drop views if they exist
DROP VIEW IF EXISTS analytics.v_customer_rfm CASCADE;
DROP VIEW IF EXISTS analytics.v_monthly_sales_trend CASCADE;
DROP VIEW IF EXISTS analytics.v_payment_distribution CASCADE;
DROP VIEW IF EXISTS analytics.v_product_category_profitability CASCADE;
DROP VIEW IF EXISTS analytics.v_seller_performance CASCADE;
DROP VIEW IF EXISTS analytics.v_geographic_performance CASCADE;
DROP VIEW IF EXISTS analytics.v_kpi_overview CASCADE;


-- ============================================================================
-- 1. View: Executive KPI Summary
-- ============================================================================

CREATE VIEW analytics.v_kpi_overview AS
WITH revenue_orders AS (
    SELECT 
        (SELECT SUM(payment_value) FROM warehouse.fact_payments) AS total_revenue,
        (SELECT COUNT(DISTINCT order_id) FROM warehouse.fact_orders) AS total_orders,
        (SELECT COUNT(DISTINCT customer_unique_id) FROM warehouse.dim_customers) AS unique_customers_registered
),
cust_orders AS (
    SELECT c.customer_unique_id, COUNT(o.order_id) AS order_count
    FROM warehouse.fact_orders o
    JOIN warehouse.dim_customers c ON o.customer_key = c.customer_key
    GROUP BY c.customer_unique_id
),
repeat_rate AS (
    SELECT 
        ROUND(SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS repeat_purchase_rate
    FROM cust_orders
),
delays AS (
    SELECT 
        ROUND(AVG(delivery_delay_days), 2) AS average_delivery_delay_days,
        ROUND(SUM(CASE WHEN is_delayed = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS delay_orders_percentage
    FROM warehouse.fact_orders
    WHERE order_status = 'delivered' AND delivery_delay_days IS NOT NULL
)
SELECT 
    r.total_revenue,
    r.total_orders,
    ROUND(r.total_revenue / r.total_orders, 2) AS average_order_value,
    r.unique_customers_registered,
    rr.repeat_purchase_rate,
    d.average_delivery_delay_days,
    d.delay_orders_percentage
FROM revenue_orders r
CROSS JOIN repeat_rate rr
CROSS JOIN delays d;


-- ============================================================================
-- 2. View: Geographic Performance (by customer state & city)
-- ============================================================================

CREATE VIEW analytics.v_geographic_performance AS
SELECT 
    c.customer_state,
    c.customer_city,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COALESCE(SUM(p.payment_value), 0) AS total_revenue,
    ROUND(COALESCE(SUM(p.payment_value), 0) / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS average_order_value
FROM warehouse.fact_orders o
JOIN warehouse.dim_customers c ON o.customer_key = c.customer_key
LEFT JOIN warehouse.fact_payments p ON o.order_id = p.order_id
GROUP BY c.customer_state, c.customer_city;


-- ============================================================================
-- 3. View: Seller Performance
-- ============================================================================

CREATE VIEW analytics.v_seller_performance AS
SELECT 
    s.seller_id,
    s.seller_city,
    s.seller_state,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    SUM(oi.price) AS total_item_revenue,
    ROUND(AVG(r.review_score), 2) AS average_review_score,
    ROUND(AVG(o.delivery_delay_days), 2) AS average_delivery_delay_days
FROM warehouse.dim_sellers s
JOIN warehouse.fact_order_items oi ON s.seller_key = oi.seller_key
JOIN warehouse.fact_orders o ON oi.order_id = o.order_id
LEFT JOIN warehouse.fact_reviews r ON o.order_id = r.order_id
GROUP BY s.seller_id, s.seller_city, s.seller_state;


-- ============================================================================
-- 4. View: Product Category Profitability
-- ============================================================================

CREATE VIEW analytics.v_product_category_profitability AS
SELECT 
    COALESCE(p.product_category_name_english, p.product_category_name, 'unknown') AS product_category,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    COUNT(oi.order_item_key) AS items_sold,
    SUM(oi.price) AS total_revenue,
    ROUND(AVG(oi.price), 2) AS average_item_price,
    ROUND(AVG(r.review_score), 2) AS average_review_score
FROM warehouse.dim_products p
JOIN warehouse.fact_order_items oi ON p.product_key = oi.product_key
LEFT JOIN warehouse.fact_reviews r ON oi.order_id = r.order_id
GROUP BY p.product_category_name_english, p.product_category_name;


-- ============================================================================
-- 5. View: Payment Distribution
-- ============================================================================

CREATE VIEW analytics.v_payment_distribution AS
SELECT 
    payment_type,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(*) AS transactions_count,
    SUM(payment_value) AS total_payment_value,
    ROUND(SUM(payment_value) * 100.0 / (SELECT SUM(payment_value) FROM warehouse.fact_payments), 2) AS value_percentage
FROM warehouse.fact_payments
GROUP BY payment_type;


-- ============================================================================
-- 6. View: Monthly Sales Trend
-- ============================================================================

CREATE VIEW analytics.v_monthly_sales_trend AS
SELECT 
    d.year,
    d.month,
    d.month_name,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(p.payment_value) AS total_revenue
FROM warehouse.fact_orders o
JOIN warehouse.dim_date d ON o.purchase_date_key = d.date_key
LEFT JOIN warehouse.fact_payments p ON o.order_id = p.order_id
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;


-- ============================================================================
-- 7. View: Customer RFM Metrics (Recency, Frequency, Monetary)
-- ============================================================================

CREATE VIEW analytics.v_customer_rfm AS
WITH last_order_date AS (
    SELECT MAX(purchase_timestamp) AS max_date FROM warehouse.fact_orders
),
cust_metrics AS (
    SELECT 
        c.customer_unique_id,
        EXTRACT(DAY FROM ((SELECT max_date FROM last_order_date) - MAX(o.purchase_timestamp)))::INT AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        COALESCE(SUM(p.payment_value), 0) AS monetary_value
    FROM warehouse.dim_customers c
    JOIN warehouse.fact_orders o ON c.customer_key = o.customer_key
    LEFT JOIN warehouse.fact_payments p ON o.order_id = p.order_id
    GROUP BY c.customer_unique_id
)
SELECT 
    customer_unique_id,
    recency_days,
    frequency,
    monetary_value
FROM cust_metrics;
