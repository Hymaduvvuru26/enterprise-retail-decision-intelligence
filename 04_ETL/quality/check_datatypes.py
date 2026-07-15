import pandas as pd
from config.database import get_connection
import importlib
logger = importlib.import_module("04_ETL.logger").logger

def check_value_constraints(schema="staging"):
    """
    Executes specific constraint and range checks on staging tables.
    Returns a summary DataFrame of violations.
    """
    logger.info("Running quality checks: Value Constraints and Datatypes")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Define validation rules
    rules = [
        {
            "Rule Name": "Review score between 1 and 5",
            "Table": "order_reviews",
            "Column": "review_score",
            "SQL Check": "review_score < 1 OR review_score > 5"
        },
        {
            "Rule Name": "Non-negative item price",
            "Table": "order_items",
            "Column": "price",
            "SQL Check": "price < 0"
        },
        {
            "Rule Name": "Non-negative freight value",
            "Table": "order_items",
            "Column": "freight_value",
            "SQL Check": "freight_value < 0"
        },
        {
            "Rule Name": "Non-negative payment value",
            "Table": "order_payments",
            "Column": "payment_value",
            "SQL Check": "payment_value < 0"
        },
        {
            "Rule Name": "Non-negative payment installments",
            "Table": "order_payments",
            "Column": "payment_installments",
            "SQL Check": "payment_installments < 0"
        },
        {
            "Rule Name": "Approval timestamp >= purchase timestamp",
            "Table": "orders",
            "Column": "order_approved_at",
            "SQL Check": "order_approved_at < order_purchase_timestamp"
        },
        {
            "Rule Name": "Delivery timestamp >= purchase timestamp",
            "Table": "orders",
            "Column": "order_delivered_customer_date",
            "SQL Check": "order_delivered_customer_date < order_purchase_timestamp"
        }
    ]
    
    results = []
    
    for rule in rules:
        table = rule["Table"]
        check = rule["SQL Check"]
        col = rule["Column"]
        
        try:
            # First check if the table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = %s
                );
            """, (schema, table))
            if not cursor.fetchone()[0]:
                continue
                
            # Count total rows
            cursor.execute(f"SELECT COUNT(*) FROM {schema}.\"{table}\";")
            total_rows = cursor.fetchone()[0]
            
            # Count violating rows
            query = f"SELECT COUNT(*) FROM {schema}.\"{table}\" WHERE {check};"
            cursor.execute(query)
            violation_count = cursor.fetchone()[0]
            
            violation_pct = round((violation_count / total_rows * 100), 2) if total_rows > 0 else 0.0
            
            results.append({
                "Rule Name": rule["Rule Name"],
                "Table": table,
                "Column": col,
                "Total Rows": total_rows,
                "Violations Count": violation_count,
                "Violation %": violation_pct,
                "SQL Constraint": check
            })
            
        except Exception as e:
            logger.error(f"Error checking datatype constraints on {schema}.{table}.{col}: {e}")
            conn.rollback()
            
    cursor.close()
    conn.close()
    
    return pd.DataFrame(results)

if __name__ == "__main__":
    df = check_value_constraints()
    print(df[df["Violations Count"] > 0])
