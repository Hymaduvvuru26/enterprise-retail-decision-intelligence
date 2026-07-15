import pandas as pd
from config.database import get_connection
import importlib
logger = importlib.import_module("04_ETL.logger").logger

def get_table_columns(cursor, schema, table):
    """Retrieves column names for a given table from information_schema."""
    query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = %s;
    """
    cursor.execute(query, (schema, table))
    return [row[0] for row in cursor.fetchall()]

def check_missing_values(schema="staging"):
    """
    Queries all staging tables, checks for missing (NULL) values in each column,
    and returns a summary DataFrame.
    """
    logger.info("Running quality checks: Missing Values")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all tables in the staging schema
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s;
    """, (schema,))
    tables = [row[0] for row in cursor.fetchall()]
    
    results = []
    
    for table in tables:
        try:
            columns = get_table_columns(cursor, schema, table)
            if not columns:
                continue
                
            # Build union query for all columns in this table
            select_parts = []
            for col in columns:
                select_parts.append(
                    f"SELECT '{col}' AS column_name, "
                    f"COUNT(*) - COUNT(\"{col}\") AS missing_count, "
                    f"COUNT(*) AS total_count "
                    f"FROM {schema}.\"{table}\""
                )
            
            union_query = " UNION ALL ".join(select_parts)
            
            cursor.execute(union_query)
            rows = cursor.fetchall()
            
            for row in rows:
                col_name, missing_count, total_count = row
                missing_pct = round((missing_count / total_count * 100), 2) if total_count > 0 else 0.0
                results.append({
                    "Schema": schema,
                    "Table": table,
                    "Column": col_name,
                    "Missing Count": missing_count,
                    "Total Count": total_count,
                    "Missing %": missing_pct
                })
        except Exception as e:
            logger.error(f"Error checking missing values on {schema}.{table}: {e}")
            conn.rollback()
            
    cursor.close()
    conn.close()
    
    return pd.DataFrame(results)

if __name__ == "__main__":
    df = check_missing_values()
    print(df[df["Missing Count"] > 0])
