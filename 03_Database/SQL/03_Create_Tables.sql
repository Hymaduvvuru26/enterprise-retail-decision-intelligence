-- ============================================================================
-- Enterprise Retail Decision Intelligence Platform
-- Script 03: Create Tables (Staging & Warehouse Schemas)
-- ============================================================================

-- Drop staging tables if they exist
DROP TABLE IF EXISTS staging.customers CASCADE;
DROP TABLE IF EXISTS staging.geolocation CASCADE;
DROP TABLE IF EXISTS staging.orders CASCADE;
DROP TABLE IF EXISTS staging.order_items CASCADE;
DROP TABLE IF EXISTS staging.order_payments CASCADE;
DROP TABLE IF EXISTS staging.order_reviews CASCADE;
DROP TABLE IF EXISTS staging.products CASCADE;
DROP TABLE IF EXISTS staging.sellers CASCADE;
DROP TABLE IF EXISTS staging.category_translation CASCADE;

-- Drop warehouse tables if they exist
DROP TABLE IF EXISTS warehouse.fact_order_items CASCADE;
DROP TABLE IF EXISTS warehouse.fact_payments CASCADE;
DROP TABLE IF EXISTS warehouse.fact_reviews CASCADE;
DROP TABLE IF EXISTS warehouse.fact_orders CASCADE;
DROP TABLE IF EXISTS warehouse.dim_customers CASCADE;
DROP TABLE IF EXISTS warehouse.dim_sellers CASCADE;
DROP TABLE IF EXISTS warehouse.dim_products CASCADE;
DROP TABLE IF EXISTS warehouse.dim_date CASCADE;


-- ============================================================================
-- 1. STAGING SCHEMA TABLES (Raw representations of CSV files)
-- ============================================================================

CREATE TABLE staging.customers (
    customer_id VARCHAR(50),
    customer_unique_id VARCHAR(50),
    customer_zip_code_prefix VARCHAR(20),
    customer_city VARCHAR(100),
    customer_state VARCHAR(10)
);

CREATE TABLE staging.geolocation (
    geolocation_zip_code_prefix VARCHAR(20),
    geolocation_lat DOUBLE PRECISION,
    geolocation_lng DOUBLE PRECISION,
    geolocation_city VARCHAR(100),
    geolocation_state VARCHAR(10)
);

CREATE TABLE staging.orders (
    order_id VARCHAR(50),
    customer_id VARCHAR(50),
    order_status VARCHAR(50),
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);

CREATE TABLE staging.order_items (
    order_id VARCHAR(50),
    order_item_id INT,
    product_id VARCHAR(50),
    seller_id VARCHAR(50),
    shipping_limit_date TIMESTAMP,
    price DECIMAL(10, 2),
    freight_value DECIMAL(10, 2)
);

CREATE TABLE staging.order_payments (
    order_id VARCHAR(50),
    payment_sequential INT,
    payment_type VARCHAR(50),
    payment_installments INT,
    payment_value DECIMAL(10, 2)
);

CREATE TABLE staging.order_reviews (
    review_id VARCHAR(50),
    order_id VARCHAR(50),
    review_score INT,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP
);

CREATE TABLE staging.products (
    product_id VARCHAR(50),
    product_category_name VARCHAR(100),
    product_name_lenght INT,          -- matching raw CSV spelling
    product_description_lenght INT,   -- matching raw CSV spelling
    product_photos_qty INT,
    product_weight_g DOUBLE PRECISION,
    product_length_cm DOUBLE PRECISION,
    product_height_cm DOUBLE PRECISION,
    product_width_cm DOUBLE PRECISION
);

CREATE TABLE staging.sellers (
    seller_id VARCHAR(50),
    seller_zip_code_prefix VARCHAR(20),
    seller_city VARCHAR(100),
    seller_state VARCHAR(10)
);

CREATE TABLE staging.category_translation (
    product_category_name VARCHAR(100),
    product_category_name_english VARCHAR(100)
);


-- ============================================================================
-- 2. WAREHOUSE SCHEMA TABLES (Star Schema / Dimensional Model)
-- ============================================================================

-- Dimension: Date
CREATE TABLE warehouse.dim_date (
    date_key INT PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day INT NOT NULL,
    day_of_week INT NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

-- Dimension: Customers
CREATE TABLE warehouse.dim_customers (
    customer_key SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) UNIQUE NOT NULL,
    customer_unique_id VARCHAR(50) NOT NULL,
    customer_zip_code_prefix VARCHAR(20),
    customer_city VARCHAR(100),
    customer_state VARCHAR(10)
);

-- Dimension: Sellers
CREATE TABLE warehouse.dim_sellers (
    seller_key SERIAL PRIMARY KEY,
    seller_id VARCHAR(50) UNIQUE NOT NULL,
    seller_zip_code_prefix VARCHAR(20),
    seller_city VARCHAR(100),
    seller_state VARCHAR(10)
);

-- Dimension: Products (Spelling corrected and Category translation integrated)
CREATE TABLE warehouse.dim_products (
    product_key SERIAL PRIMARY KEY,
    product_id VARCHAR(50) UNIQUE NOT NULL,
    product_category_name VARCHAR(100),
    product_category_name_english VARCHAR(100),
    product_weight_g DOUBLE PRECISION,
    product_length_cm DOUBLE PRECISION,
    product_height_cm DOUBLE PRECISION,
    product_width_cm DOUBLE PRECISION
);

-- Fact: Orders (Header level facts)
CREATE TABLE warehouse.fact_orders (
    order_key SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    customer_key INT NOT NULL REFERENCES warehouse.dim_customers(customer_key),
    order_status VARCHAR(50) NOT NULL,
    purchase_date_key INT NOT NULL REFERENCES warehouse.dim_date(date_key),
    purchase_timestamp TIMESTAMP NOT NULL,
    approved_timestamp TIMESTAMP,
    delivered_carrier_timestamp TIMESTAMP,
    delivered_customer_timestamp TIMESTAMP,
    estimated_delivery_timestamp TIMESTAMP,
    delivery_delay_days INT,
    is_delayed BOOLEAN
);

-- Fact: Order Items (Line item details)
CREATE TABLE warehouse.fact_order_items (
    order_item_key SERIAL PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    order_item_id INT NOT NULL,
    product_key INT NOT NULL REFERENCES warehouse.dim_products(product_key),
    seller_key INT NOT NULL REFERENCES warehouse.dim_sellers(seller_key),
    shipping_limit_date TIMESTAMP NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    freight_value DECIMAL(10, 2) NOT NULL
);

-- Fact: Payments (Order payment methods & distribution)
CREATE TABLE warehouse.fact_payments (
    payment_key SERIAL PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    payment_sequential INT NOT NULL,
    payment_type VARCHAR(50) NOT NULL,
    payment_installments INT NOT NULL,
    payment_value DECIMAL(10, 2) NOT NULL
);

-- Fact: Reviews (Customer reviews & feedback scores)
CREATE TABLE warehouse.fact_reviews (
    review_key SERIAL PRIMARY KEY,
    review_id VARCHAR(50) NOT NULL,
    order_id VARCHAR(50) NOT NULL,
    review_score INT NOT NULL,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_timestamp TIMESTAMP NOT NULL,
    review_answer_timestamp TIMESTAMP NOT NULL
);
