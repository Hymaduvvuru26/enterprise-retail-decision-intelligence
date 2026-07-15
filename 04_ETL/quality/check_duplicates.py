import pandas as pd
from config.database import get_connection
import importlib
logger = importlib.import_module("04_ETL.logger").logger

# Defined primary/unique keys for staging validation
STAGING_KEYS = {
    "customers": ["customer_id"],
    "orders": ["order_id"],
    "order_items": ["order_id", "order_item_id"],
    "products": ["product_id"],
    "sellers": ["seller_id"],
    "order_reviews": ["review_id"],
    "order_payments": ["order_id", "payment_sequential"],
    "category_translation": ["product_category_name"],
    "geolocation": ["geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng"]
}

def check_duplicates(schema="staging"):
    """
    Checks each staging table for primary/unique key duplicate violations.
    Returns a summary DataFrame.
    """
    logger.info("Running quality checks: Duplicate Rows")
    conn = get_connection()
    cursor = conn.cursor()
    
    results = []
    
    for table, keys in STAGING_KEYS.items():
        try:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = %s
                );
            """, (schema, table))
            if not cursor.fetchone()[0]:
                continue
                
            # Build query to count total and unique rows based on key columns
            keys_str = ", ".join(f'"{k}"' for k in keys)
            
            # Using tuple distinct count for composite keys: COUNT(DISTINCT ROW(col1, col2))
            query = f"""
                SELECT 
                    COUNT(*) AS total_rows,
                    COUNT(*) - COUNT(DISTINCT ROW({keys_str})) AS duplicate_rows
                FROM {schema}."{table}";
            """
            
            cursor.execute(query)
            total_rows, duplicate_rows = cursor.fetchone()
            
            dup_pct = round((duplicate_rows / total_rows * 100), 2) if total_rows > 0 else 0.0
            
            results.append({
                "Schema": schema,
                "Table": table,
                "Unique Keys": ", ".join(keys),
                "Total Rows": total_rows,
                "Duplicate Rows": duplicate_rows,
                "Duplicate %": dup_pct
            })
            
        except Exception as e:
            logger.error(f"Error checking duplicates on {schema}.{table}: {e}")
            conn.rollback()
            
    cursor.close()
    conn.close()
    
    return pd.DataFrame(results)

if __name__ == "__main__":
    df = check_duplicates()
    print(df[df["Duplicate Rows"] > 0])
