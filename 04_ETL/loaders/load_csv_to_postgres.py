from pathlib import Path
from config.constants import RAW_DATA, STAGING_SCHEMA
from config.dataset_mapping import DATASETS
from config.settings import BATCH_SIZE
from .csv_loader import load_csv
from ..logger import logger

# Map dataset keys to database staging table names
TABLE_MAPPING = {
    "customers": "customers",
    "orders": "orders",
    "order_items": "order_items",
    "payments": "order_payments",
    "reviews": "order_reviews",
    "products": "products",
    "sellers": "sellers",
    "geolocation": "geolocation",
    "category_translation": "category_translation"
}

def run_etl():
    logger.info("Starting ETL Pipeline: Raw CSV to Staging PostgreSQL")
    print("=" * 60)
    print("STARTING ETL PIPELINE: RAW CSV TO STAGING POSTGRESQL")
    print("=" * 60)
    
    success = True
    total_loaded = 0
    
    for key, filename in DATASETS.items():
        table_name = TABLE_MAPPING.get(key)
        if not table_name:
            logger.error(f"No table mapping found for dataset key: {key}")
            success = False
            continue
            
        csv_file_path = RAW_DATA / filename
        
        print(f"\nProcessing '{key}' dataset...")
        print(f"Source file: {csv_file_path.name}")
        print(f"Target table: {STAGING_SCHEMA}.{table_name}")
        
        try:
            loaded_rows = load_csv(
                file_path=str(csv_file_path),
                table_name=table_name,
                schema=STAGING_SCHEMA,
                batch_size=BATCH_SIZE
            )
            total_loaded += loaded_rows
            print(f"--> Success! Loaded {loaded_rows} rows.")
        except Exception as e:
            logger.error(f"Failed to load dataset '{key}': {e}")
            print(f"--> FAILED! Check logs for details: {e}")
            success = False
            
    print("\n" + "=" * 60)
    if success:
        logger.info(f"ETL pipeline finished successfully. Total rows loaded: {total_loaded}")
        print(f"ETL PIPELINE FINISHED SUCCESSFULLY! Total rows loaded: {total_loaded}")
    else:
        logger.warning("ETL pipeline finished with errors. See log file for details.")
        print("ETL PIPELINE FINISHED WITH ERRORS. Check 04_ETL/logs/etl.log.")
    print("=" * 60)

if __name__ == "__main__":
    run_etl()
