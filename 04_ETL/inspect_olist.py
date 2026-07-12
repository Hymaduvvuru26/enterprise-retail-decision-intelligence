from pathlib import Path
import pandas as pd

# ----------------------------------------
# Project Paths
# ----------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OLIST_PATH = PROJECT_ROOT / "02_Data" / "Raw" / "Olist"

REPORT_PATH = PROJECT_ROOT / "10_Reports" / "Data_Quality"

REPORT_PATH.mkdir(parents=True, exist_ok=True)

# ----------------------------------------
# Find all CSV files
# ----------------------------------------

csv_files = sorted(OLIST_PATH.glob("*.csv"))

print("=" * 60)
print("OLIST DATASET INSPECTION")
print("=" * 60)

summary = []

for file in csv_files:

    print(f"\nReading {file.name}")

    df = pd.read_csv(file)

    rows = len(df)
    cols = len(df.columns)

    duplicates = df.duplicated().sum()

    missing = df.isnull().sum().sum()

    memory = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)

    summary.append(
        {
            "Dataset": file.name,
            "Rows": rows,
            "Columns": cols,
            "Missing Values": missing,
            "Duplicate Rows": duplicates,
            "Memory (MB)": memory,
        }
    )

summary_df = pd.DataFrame(summary)

print("\n")
print(summary_df)

summary_df.to_csv(
    REPORT_PATH / "olist_data_quality_summary.csv",
    index=False,
)

summary_df.to_excel(
    REPORT_PATH / "olist_data_quality_summary.xlsx",
    index=False,
)

print("\nReports generated successfully.")