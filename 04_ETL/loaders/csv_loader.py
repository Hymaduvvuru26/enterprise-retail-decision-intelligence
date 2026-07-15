import pandas as pd
from sqlalchemy import text
from config.database import get_engine
import importlib
logger = importlib.import_module("04_ETL.logger").logger
import os

def load_csv(file_path, table_name, schema="staging", batch_size=5000):
    """
    Reads a CSV file and appends it to a PostgreSQL table in the specified schema.
    Truncates the table before loading to ensure idempotency.
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
        
    logger.info(f"Starting to load {file_path} into {schema}.{table_name}...")
    
    engine = get_engine()
    
    # Truncate table first to ensure idempotency and clean reload
    with engine.begin() as conn:
        logger.info(f"Truncating table {schema}.{table_name}")
        conn.execute(text(f"TRUNCATE TABLE {schema}.{table_name} CASCADE;"))
    
    # Read and load in chunks
    chunk_count = 0
    total_rows = 0
    
    for chunk in pd.read_csv(file_path, chunksize=batch_size):
        # Convert date columns to datetime objects
        date_cols = [c for c in chunk.columns if 'date' in c or 'time' in c or 'approved_at' in c]
        for col in date_cols:
            chunk[col] = pd.to_datetime(chunk[col], errors='coerce')
            
        # Strip string columns to avoid leading/trailing spaces
        for col in chunk.select_dtypes(include=['object']).columns:
            chunk[col] = chunk[col].astype(str).str.strip()
            # Convert empty string representations back to None so they load as NULL in Postgres
            chunk[col] = chunk[col].replace({'': None, 'nan': None, 'NaN': None, 'None': None})
            
        chunk.to_sql(
            name=table_name,
            con=engine,
            schema=schema,
            if_exists="append",
            index=False
        )
        chunk_count += 1
        total_rows += len(chunk)
        logger.info(f"Loaded chunk {chunk_count} with {len(chunk)} rows into {schema}.{table_name}")
        
    logger.info(f"Successfully loaded {total_rows} rows from {file_path} into {schema}.{table_name}")
    return total_rows
