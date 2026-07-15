import time
from config.database import get_connection
import importlib
logger = importlib.import_module("04_ETL.logger").logger

def load_warehouse():
    """
    Orchestrates the transformation and loading of clean data from the staging schema
    into the warehouse schema star tables.
    """
    logger.info("Starting warehouse data loading & transformation...")
    print("=" * 60)
    print("STARTING WAREHOUSE DATA LOADING & TRANSFORMATION")
    print("=" * 60)
    
    start_time = time.time()
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Truncate existing warehouse data in correct dependency order
    truncates = [
        "TRUNCATE TABLE warehouse.fact_order_items CASCADE;",
        "TRUNCATE TABLE warehouse.fact_payments CASCADE;",
        "TRUNCATE TABLE warehouse.fact_reviews CASCADE;",
        "TRUNCATE TABLE warehouse.fact_orders CASCADE;",
        "TRUNCATE TABLE warehouse.dim_customers CASCADE;",
        "TRUNCATE TABLE warehouse.dim_sellers CASCADE;",
        "TRUNCATE TABLE warehouse.dim_products CASCADE;",
        "TRUNCATE TABLE warehouse.dim_date CASCADE;"
    ]
    
    # 2. Ingestion steps
    steps = [
        # Step A: Generate Dim Date range
        {
            "desc": "Generating Date Dimension (warehouse.dim_date)",
            "sql": """
                INSERT INTO warehouse.dim_date (
                    date_key, date, year, quarter, month, month_name, day, day_of_week, day_name, is_weekend
                )
                SELECT 
                    TO_CHAR(d, 'YYYYMMDD')::INT AS date_key,
                    d::DATE AS date,
                    EXTRACT(YEAR FROM d)::INT AS year,
                    EXTRACT(QUARTER FROM d)::INT AS quarter,
                    EXTRACT(MONTH FROM d)::INT AS month,
                    TRIM(TO_CHAR(d, 'Month')) AS month_name,
                    EXTRACT(DAY FROM d)::INT AS day,
                    EXTRACT(ISODOW FROM d)::INT AS day_of_week,
                    TRIM(TO_CHAR(d, 'Day')) AS day_name,
                    CASE WHEN EXTRACT(ISODOW FROM d) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend
                FROM generate_series('2016-01-01'::TIMESTAMP, '2019-12-31'::TIMESTAMP, '1 day'::interval) d
                ON CONFLICT (date_key) DO NOTHING;
            """
        },
        # Step B: Load Dim Customers
        {
            "desc": "Loading Customers Dimension (warehouse.dim_customers)",
            "sql": """
                INSERT INTO warehouse.dim_customers (
                    customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state
                )
                SELECT DISTINCT 
                    customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state
                FROM staging.customers
                WHERE customer_id IS NOT NULL
                ON CONFLICT (customer_id) DO NOTHING;
            """
        },
        # Step C: Load Dim Sellers
        {
            "desc": "Loading Sellers Dimension (warehouse.dim_sellers)",
            "sql": """
                INSERT INTO warehouse.dim_sellers (
                    seller_id, seller_zip_code_prefix, seller_city, seller_state
                )
                SELECT DISTINCT 
                    seller_id, seller_zip_code_prefix, seller_city, seller_state
                FROM staging.sellers
                WHERE seller_id IS NOT NULL
                ON CONFLICT (seller_id) DO NOTHING;
            """
        },
        # Step D: Load Dim Products
        {
            "desc": "Loading Products Dimension (warehouse.dim_products)",
            "sql": """
                INSERT INTO warehouse.dim_products (
                    product_id, product_category_name, product_category_name_english, 
                    product_weight_g, product_length_cm, product_height_cm, product_width_cm
                )
                SELECT DISTINCT 
                    p.product_id, 
                    p.product_category_name, 
                    COALESCE(t.product_category_name_english, p.product_category_name) AS product_category_name_english,
                    p.product_weight_g, 
                    p.product_length_cm, 
                    p.product_height_cm, 
                    p.product_width_cm
                FROM staging.products p
                LEFT JOIN staging.category_translation t ON p.product_category_name = t.product_category_name
                WHERE p.product_id IS NOT NULL
                ON CONFLICT (product_id) DO NOTHING;
            """
        },
        # Step E: Load Fact Orders
        {
            "desc": "Loading Orders Fact (warehouse.fact_orders)",
            "sql": """
                INSERT INTO warehouse.fact_orders (
                    order_id, customer_key, order_status, purchase_date_key, purchase_timestamp, 
                    approved_timestamp, delivered_carrier_timestamp, delivered_customer_timestamp, 
                    estimated_delivery_timestamp, delivery_delay_days, is_delayed
                )
                SELECT DISTINCT
                    o.order_id,
                    c.customer_key,
                    o.order_status,
                    TO_CHAR(o.order_purchase_timestamp, 'YYYYMMDD')::INT AS purchase_date_key,
                    o.order_purchase_timestamp,
                    o.order_approved_at,
                    o.order_delivered_carrier_date,
                    o.order_delivered_customer_date,
                    o.order_estimated_delivery_date,
                    EXTRACT(DAY FROM (o.order_delivered_customer_date - o.order_estimated_delivery_date))::INT AS delivery_delay_days,
                    CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN TRUE ELSE FALSE END AS is_delayed
                FROM staging.orders o
                JOIN warehouse.dim_customers c ON o.customer_id = c.customer_id
                JOIN warehouse.dim_date d ON TO_CHAR(o.order_purchase_timestamp, 'YYYYMMDD')::INT = d.date_key
                WHERE o.order_id IS NOT NULL
                ON CONFLICT (order_id) DO NOTHING;
            """
        },
        # Step F: Load Fact Order Items
        {
            "desc": "Loading Order Items Fact (warehouse.fact_order_items)",
            "sql": """
                INSERT INTO warehouse.fact_order_items (
                    order_id, order_item_id, product_key, seller_key, shipping_limit_date, price, freight_value
                )
                SELECT 
                    oi.order_id,
                    oi.order_item_id,
                    p.product_key,
                    s.seller_key,
                    oi.shipping_limit_date,
                    oi.price,
                    oi.freight_value
                FROM staging.order_items oi
                JOIN warehouse.dim_products p ON oi.product_id = p.product_id
                JOIN warehouse.dim_sellers s ON oi.seller_id = s.seller_id;
            """
        },
        # Step G: Load Fact Payments
        {
            "desc": "Loading Payments Fact (warehouse.fact_payments)",
            "sql": """
                INSERT INTO warehouse.fact_payments (
                    order_id, payment_sequential, payment_type, payment_installments, payment_value
                )
                SELECT 
                    order_id,
                    payment_sequential,
                    payment_type,
                    payment_installments,
                    payment_value
                FROM staging.order_payments;
            """
        },
        # Step H: Load Fact Reviews
        {
            "desc": "Loading Reviews Fact (warehouse.fact_reviews)",
            "sql": """
                INSERT INTO warehouse.fact_reviews (
                    review_id, order_id, review_score, review_comment_title, review_comment_message, 
                    review_creation_timestamp, review_answer_timestamp
                )
                SELECT 
                    review_id,
                    order_id,
                    review_score,
                    review_comment_title,
                    review_comment_message,
                    review_creation_date,
                    review_answer_timestamp
                FROM staging.order_reviews;
            """
        }
    ]
    
    try:
        # Perform truncates
        print("Resetting warehouse tables...")
        for truncate_sql in truncates:
            cursor.execute(truncate_sql)
        
        # Execute load steps
        for step in steps:
            print(f"--> {step['desc']}...")
            step_start = time.time()
            cursor.execute(step["sql"])
            rows_inserted = cursor.rowcount
            step_duration = round(time.time() - step_start, 2)
            logger.info(f"{step['desc']}: successfully loaded {rows_inserted} rows in {step_duration}s.")
            print(f"    Done ({rows_inserted} rows loaded in {step_duration}s)")
            
        # Commit transaction
        conn.commit()
        total_duration = round(time.time() - start_time, 2)
        print("\n" + "=" * 60)
        print(f"WAREHOUSE LOAD COMPLETED SUCCESSFULLY IN {total_duration}s!")
        print("=" * 60)
        logger.info(f"Warehouse transaction committed successfully in {total_duration}s.")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to load data into warehouse: {e}")
        print("\n" + "=" * 60)
        print(f"WAREHOUSE LOAD TRANSACTION FAILED: {e}")
        print("Rolling back changes.")
        print("=" * 60)
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    load_warehouse()
