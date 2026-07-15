-- ============================================================================
-- Enterprise Retail Decision Intelligence Platform
-- Script 04: Create Indexes (Staging & Warehouse Optimization)
-- ============================================================================

-- Drop warehouse indexes if they exist
DROP INDEX IF EXISTS warehouse.idx_dim_customers_id;
DROP INDEX IF EXISTS warehouse.idx_dim_sellers_id;
DROP INDEX IF EXISTS warehouse.idx_dim_products_id;
DROP INDEX IF EXISTS warehouse.idx_fact_orders_id;
DROP INDEX IF EXISTS warehouse.idx_fact_orders_customer;
DROP INDEX IF EXISTS warehouse.idx_fact_orders_date;
DROP INDEX IF EXISTS warehouse.idx_fact_order_items_order;
DROP INDEX IF EXISTS warehouse.idx_fact_order_items_product;
DROP INDEX IF EXISTS warehouse.idx_fact_order_items_seller;
DROP INDEX IF EXISTS warehouse.idx_fact_payments_order;
DROP INDEX IF EXISTS warehouse.idx_fact_reviews_order;

-- Drop staging indexes if they exist
DROP INDEX IF EXISTS staging.idx_staging_customers_id;
DROP INDEX IF EXISTS staging.idx_staging_sellers_id;
DROP INDEX IF EXISTS staging.idx_staging_products_id;
DROP INDEX IF EXISTS staging.idx_staging_orders_id;
DROP INDEX IF EXISTS staging.idx_staging_order_items_order;
DROP INDEX IF EXISTS staging.idx_staging_order_payments_order;
DROP INDEX IF EXISTS staging.idx_staging_order_reviews_order;


-- ============================================================================
-- 1. STAGING SCHEMAS INDEXES (Optimizes transformation ETL joins)
-- ============================================================================

CREATE INDEX idx_staging_customers_id ON staging.customers (customer_id);
CREATE INDEX idx_staging_sellers_id ON staging.sellers (seller_id);
CREATE INDEX idx_staging_products_id ON staging.products (product_id);
CREATE INDEX idx_staging_orders_id ON staging.orders (order_id);
CREATE INDEX idx_staging_order_items_order ON staging.order_items (order_id, product_id, seller_id);
CREATE INDEX idx_staging_order_payments_order ON staging.order_payments (order_id);
CREATE INDEX idx_staging_order_reviews_order ON staging.order_reviews (order_id);


-- ============================================================================
-- 2. WAREHOUSE SCHEMAS INDEXES (Optimizes business dashboard queries)
-- ============================================================================

-- Unique business lookup indexes on dimensions
CREATE INDEX idx_dim_customers_id ON warehouse.dim_customers (customer_id);
CREATE INDEX idx_dim_sellers_id ON warehouse.dim_sellers (seller_id);
CREATE INDEX idx_dim_products_id ON warehouse.dim_products (product_id);

-- Foreign key indexes on Fact Orders
CREATE INDEX idx_fact_orders_id ON warehouse.fact_orders (order_id);
CREATE INDEX idx_fact_orders_customer ON warehouse.fact_orders (customer_key);
CREATE INDEX idx_fact_orders_date ON warehouse.fact_orders (purchase_date_key);

-- Foreign key & composite indexes on Fact Order Items
CREATE INDEX idx_fact_order_items_order ON warehouse.fact_order_items (order_id);
CREATE INDEX idx_fact_order_items_product ON warehouse.fact_order_items (product_key);
CREATE INDEX idx_fact_order_items_seller ON warehouse.fact_order_items (seller_key);

-- Foreign key indexes on Fact Payments & Reviews
CREATE INDEX idx_fact_payments_order ON warehouse.fact_payments (order_id);
CREATE INDEX idx_fact_reviews_order ON warehouse.fact_reviews (order_id);
