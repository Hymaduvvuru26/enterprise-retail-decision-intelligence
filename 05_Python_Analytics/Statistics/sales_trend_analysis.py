import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from config.database import get_engine
import importlib
logger = importlib.import_module("04_ETL.logger").logger

def run_sales_trend_analysis():
    logger.info("Starting monthly sales trend analysis...")
    print("=" * 60)
    print("RUNNING MONTHLY SALES TREND ANALYSIS")
    print("=" * 60)
    
    engine = get_engine()
    
    # 1. Fetch monthly trend data
    query = "SELECT * FROM analytics.v_monthly_sales_trend;"
    logger.info("Fetching monthly sales trend from database...")
    trend = pd.read_sql(query, con=engine)
    
    if trend.empty:
        logger.warning("No sales trend data found. Make sure the database is loaded.")
        print("No sales trend data found.")
        return
        
    # Create Date/Period column for visualization label, e.g. "2017-01"
    trend['Period'] = trend['year'].astype(str) + '-' + trend['month'].astype(str).str.zfill(2)
    trend = trend.sort_values(by='Period').reset_index(drop=True)
    
    # 2. Calculate Growth Rates
    trend['MoM_Revenue_Growth_%'] = round(trend['total_revenue'].pct_change() * 100, 2)
    trend['Rolling_Avg_3M_Revenue'] = round(trend['total_revenue'].rolling(window=3).mean(), 2)
    
    print("\nMonthly Sales Trend & Growth Rates:")
    print(trend[['Period', 'total_orders', 'total_revenue', 'MoM_Revenue_Growth_%']])
    
    # 3. Save metrics report
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    csv_path = PROJECT_ROOT / "10_Reports" / "SQL_Reports"
    csv_path.mkdir(parents=True, exist_ok=True)
    trend.to_csv(csv_path / "monthly_sales_growth.csv", index=False)
    print(f"\nSaved monthly trend records to {csv_path / 'monthly_sales_growth.csv'}")
    
    # 4. Generate Plot
    img_path = PROJECT_ROOT / "10_Reports" / "Dashboard"
    img_path.mkdir(parents=True, exist_ok=True)
    
    # Create double Y-axis plot
    fig, ax1 = plt.subplots(figsize=(14, 7))
    sns.set_theme(style="whitegrid")
    
    # Bar Chart for Order Counts (left y-axis)
    color1 = '#3498db'
    ax1.set_xlabel('Month (Period)', fontsize=12, labelpad=12)
    ax1.set_ylabel('Number of Orders', color=color1, fontsize=12, labelpad=12)
    bars = ax1.bar(
        trend['Period'], 
        trend['total_orders'], 
        color=color1, 
        alpha=0.6, 
        label='Monthly Orders'
    )
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.set_xticklabels(trend['Period'], rotation=45, ha='right')
    
    # Line Chart for Revenues (right y-axis)
    ax2 = ax1.twinx()
    color2 = '#e74c3c'
    ax2.set_ylabel('Total Revenue (BRL)', color=color2, fontsize=12, labelpad=12)
    line = ax2.plot(
        trend['Period'], 
        trend['total_revenue'], 
        color=color2, 
        marker='o', 
        linewidth=2.5, 
        label='Monthly Revenue'
    )
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # Optional 3-month moving average line
    line_ma = ax2.plot(
        trend['Period'], 
        trend['Rolling_Avg_3M_Revenue'], 
        color='#2ecc71', 
        linestyle='--', 
        linewidth=1.8, 
        label='3-Month Rolling Average'
    )
    
    # Title & Legend
    plt.title('Monthly Sales Trend: Revenue vs. Volume', fontsize=15, fontweight='bold', pad=15)
    
    # Combine legends from both axes
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper left')
    
    plt.tight_layout()
    plt.savefig(img_path / "monthly_sales_trend.png", dpi=300)
    plt.close()
    
    print(f"Saved trend visualization to {img_path / 'monthly_sales_trend.png'}")
    logger.info("Monthly sales trend analysis completed successfully.")

if __name__ == "__main__":
    run_sales_trend_analysis()
