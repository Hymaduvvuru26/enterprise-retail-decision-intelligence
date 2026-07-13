from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA = PROJECT_ROOT / "02_Data" / "Raw" / "Olist"

STAGING_SCHEMA = "staging"

WAREHOUSE_SCHEMA = "warehouse"

ANALYTICS_SCHEMA = "analytics"