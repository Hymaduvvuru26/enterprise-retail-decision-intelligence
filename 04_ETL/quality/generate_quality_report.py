from pathlib import Path
import pandas as pd
from datetime import datetime
from .check_missing import check_missing_values
from .check_duplicates import check_duplicates
from .check_datatypes import check_value_constraints
from ..logger import logger

def format_df_as_md_table(df):
    """Converts a pandas DataFrame into a markdown formatted table string."""
    if df.empty:
        return "*No issues found.*"
    return df.to_markdown(index=False)

def run_quality_checks():
    logger.info("Starting Data Quality Engine...")
    print("=" * 60)
    print("STARTING DATA QUALITY ENGINE")
    print("=" * 60)
    
    # Execute checks
    print("Evaluating missing values...")
    missing_df = check_missing_values()
    
    print("Evaluating duplicate rows...")
    dup_df = check_duplicates()
    
    print("Evaluating column value constraints...")
    constraints_df = check_value_constraints()
    
    # Output path
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    REPORT_PATH = PROJECT_ROOT / "10_Reports" / "Data_Quality"
    REPORT_PATH.mkdir(parents=True, exist_ok=True)
    
    md_file = REPORT_PATH / "data_quality_report.md"
    
    # Filter only relevant issues to report in detail
    missing_issues = missing_df[missing_df["Missing Count"] > 0]
    duplicate_issues = dup_df[dup_df["Duplicate Rows"] > 0]
    constraint_issues = constraints_df[constraints_df["Violations Count"] > 0]
    
    # Compile markdown content
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    md_content = f"""# Data Quality Report

*Generated on:* {now_str}

This report presents quality evaluations performed on raw Olist e-commerce datasets loaded into the PostgreSQL **staging** schema.

---

## 1. Executive Summary

### Staging Tables Row & Duplicate Counts
{format_df_as_md_table(dup_df)}

*Note: Duplicates in `geolocation` represent multiple lat/long readings for the same zip code prefix and are common in raw location logs. Duplicates in critical transaction logs (like `orders`, `customers`, `products`) represent potential business keys violations.*

---

## 2. Missing Values Detail

Columns with missing (NULL) values:
{format_df_as_md_table(missing_issues)}

*Analysis: Missing comments in reviews (`review_comment_title`, `review_comment_message`) are expected since comments are optional. Missing timestamps in orders represent specific order status transitions (e.g. `order_approved_at` is NULL for cancelled/unapproved orders).*

---

## 3. Duplicate Violations Detail

Staging table unique key violations:
{format_df_as_md_table(duplicate_issues)}

---

## 4. Range & Logical Constraint Violations

Logical value validation failures:
{format_df_as_md_table(constraint_issues)}

*Analysis: Delivery/approval dates occurring slightly prior to order timestamps are typically caused by server logging sync offsets. Review scores are expected to be bounded between 1 and 5.*

---
"""
    
    # Write the report
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    # Also save raw CSV metrics
    missing_df.to_csv(REPORT_PATH / "missing_values_report.csv", index=False)
    dup_df.to_csv(REPORT_PATH / "duplicate_rows_report.csv", index=False)
    constraints_df.to_csv(REPORT_PATH / "value_constraints_report.csv", index=False)
    
    print("\n" + "=" * 60)
    print("DATA QUALITY CHECKS COMPLETED SUCCESSFULLY!")
    print(f"Data quality report created: {md_file}")
    print("=" * 60)
    logger.info(f"Data Quality Report successfully written to {md_file}")

if __name__ == "__main__":
    run_quality_checks()
