import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from config.database import get_engine
import importlib
logger = importlib.import_module("04_ETL.logger").logger

def run_rfm_segmentation():
    logger.info("Starting RFM Customer Segmentation...")
    print("=" * 60)
    print("RUNNING RFM CUSTOMER SEGMENTATION")
    print("=" * 60)
    
    engine = get_engine()
    
    # 1. Load RFM metrics from analytics view
    query = "SELECT * FROM analytics.v_customer_rfm;"
    logger.info("Fetching customer RFM data from database...")
    rfm = pd.read_sql(query, con=engine)
    
    total_customers = len(rfm)
    logger.info(f"Loaded {total_customers} customer records.")
    print(f"Loaded {total_customers} customer records.")
    
    # 2. Assign RFM scores
    # Recency: lower is better -> labels 5 (recent) to 1 (old)
    rfm['R_Score'] = pd.qcut(rfm['recency_days'], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    
    # Monetary: higher is better -> labels 1 (low spend) to 5 (high spend)
    rfm['M_Score'] = pd.qcut(rfm['monetary_value'], 5, labels=[1, 2, 3, 4, 5]).astype(int)
    
    # Frequency: since ~97% of customers have only 1 order, we can't use qcut easily.
    # Instead, we define custom bounds: 1 order = score 1, 2 orders = score 3, 3+ orders = score 5
    def get_f_score(freq):
        if freq == 1:
            return 1
        elif freq == 2:
            return 3
        else:
            return 5
            
    rfm['F_Score'] = rfm['frequency'].apply(get_f_score)
    
    # 3. Classify customers into segments
    def segment_customer(row):
        r = row['R_Score']
        f = row['F_Score']
        
        if r >= 4 and f >= 4:
            return 'Champions'
        elif r >= 3 and f >= 3:
            return 'Loyal Customers'
        elif r >= 4 and f >= 2:
            return 'Potential Loyalists'
        elif r == 5 and f == 1:
            return 'New Customers'
        elif r == 4 and f == 1:
            return 'Promising'
        elif r == 3 and f == 2:
            return 'Needs Attention'
        elif r == 3 and f == 1:
            return 'About to Sleep'
        elif r <= 2 and f >= 4:
            return "Can't Lose Them"
        elif r <= 2 and f == 3:
            return 'At Risk'
        elif r == 2 and f <= 2:
            return 'Hibernating'
        else:
            return 'Lost'
            
    rfm['Segment'] = rfm.apply(segment_customer, axis=1)
    rfm['RFM_Score_Code'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)
    
    # 4. Generate segment summary metrics
    summary = rfm.groupby('Segment').agg(
        customer_count=('customer_unique_id', 'count'),
        avg_recency=('recency_days', 'mean'),
        avg_frequency=('frequency', 'mean'),
        avg_monetary=('monetary_value', 'mean'),
        total_monetary=('monetary_value', 'sum')
    ).reset_index()
    
    summary['customer_pct'] = round(summary['customer_count'] * 100 / total_customers, 2)
    summary['revenue_pct'] = round(summary['total_monetary'] * 100 / rfm['monetary_value'].sum(), 2)
    summary = summary.sort_values(by='customer_count', ascending=False)
    
    print("\nRFM Segment Distribution Summary:")
    print(summary[['Segment', 'customer_count', 'customer_pct', 'avg_monetary']])
    
    # 5. Save outputs
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    
    # CSV output directories
    csv_path = PROJECT_ROOT / "10_Reports" / "SQL_Reports"
    csv_path.mkdir(parents=True, exist_ok=True)
    rfm.to_csv(csv_path / "rfm_customer_segments.csv", index=False)
    summary.to_csv(csv_path / "rfm_segment_summary.csv", index=False)
    print(f"\nSaved segment records to {csv_path / 'rfm_customer_segments.csv'}")
    
    # Dashboard visual directories
    img_path = PROJECT_ROOT / "10_Reports" / "Dashboard"
    img_path.mkdir(parents=True, exist_ok=True)
    
    # Plot segment distribution
    plt.figure(figsize=(12, 6))
    sns.set_theme(style="whitegrid")
    
    ax = sns.barplot(
        data=summary,
        x='customer_count',
        y='Segment',
        palette='viridis',
        hue='Segment',
        legend=False
    )
    
    # Add values to the bars
    for i, p in enumerate(ax.patches):
        width = p.get_width()
        pct = summary.iloc[i]['customer_pct']
        ax.text(
            width + (total_customers * 0.005),
            p.get_y() + p.get_height() / 2,
            f"{int(width):,} ({pct}%)",
            ha='left',
            va='center',
            fontsize=10
        )
        
    plt.title('Olist Customer Segments by RFM Analysis', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Number of Customers', fontsize=11)
    plt.ylabel('Segment', fontsize=11)
    plt.tight_layout()
    
    plt.savefig(img_path / "rfm_segments.png", dpi=300)
    plt.close()
    print(f"Saved segment distribution plot to {img_path / 'rfm_segments.png'}")
    logger.info("RFM Customer Segmentation completed successfully.")

if __name__ == "__main__":
    run_rfm_segmentation()
