import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from config.database import get_engine
import importlib
logger = importlib.import_module("04_ETL.logger").logger

def run_demand_forecasting():
    logger.info("Starting AI Demand Forecasting...")
    print("=" * 60)
    print("RUNNING AI DEMAND FORECASTING (SCIKIT-LEARN)")
    print("=" * 60)
    
    engine = get_engine()
    
    # 1. Fetch daily sales
    query = """
        SELECT 
            d.date AS purchase_date,
            SUM(p.payment_value) AS revenue
        FROM warehouse.fact_orders o
        JOIN warehouse.dim_date d ON o.purchase_date_key = d.date_key
        LEFT JOIN warehouse.fact_payments p ON o.order_id = p.order_id
        GROUP BY d.date
        ORDER BY d.date;
    """
    logger.info("Fetching daily sales history from database...")
    df = pd.read_sql(query, con=engine)
    
    if df.empty:
        logger.warning("No transaction data found for forecasting.")
        print("No transaction data found. Make sure the warehouse is loaded.")
        return
        
    df['purchase_date'] = pd.to_datetime(df['purchase_date'])
    
    # 2. Resample to weekly sales (Sunday end of week) and fill gaps with 0
    weekly_sales = df.set_index('purchase_date').resample('W').sum().reset_index()
    weekly_sales['revenue'] = weekly_sales['revenue'].fillna(0.0)
    
    # Exclude very early or incomplete outer bounds (e.g. Olist has sparse data before Jan 2017 and after Aug 2018)
    weekly_sales = weekly_sales[
        (weekly_sales['purchase_date'] >= '2017-01-01') & 
        (weekly_sales['purchase_date'] <= '2018-09-05')
    ].reset_index(drop=True)
    
    if len(weekly_sales) < 15:
        logger.error("Insufficient history data for time-series splits.")
        print("Insufficient historical sales data for modeling.")
        return
        
    # 3. Engineer lag features
    weekly_sales['lag_1'] = weekly_sales['revenue'].shift(1)
    weekly_sales['lag_2'] = weekly_sales['revenue'].shift(2)
    weekly_sales['lag_3'] = weekly_sales['revenue'].shift(3)
    weekly_sales['rolling_mean_4'] = weekly_sales['revenue'].shift(1).rolling(window=4).mean()
    
    # Drop rows with NaNs caused by shift
    model_data = weekly_sales.dropna().copy()
    
    # 4. Train-Test Split (Last 8 weeks for test set evaluation)
    test_weeks = 8
    train_data = model_data.iloc[:-test_weeks]
    test_data = model_data.iloc[-test_weeks:]
    
    features = ['lag_1', 'lag_2', 'lag_3', 'rolling_mean_4']
    X_train = train_data[features]
    y_train = train_data['revenue']
    X_test = test_data[features]
    y_test = test_data['revenue']
    
    # 5. Train model
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    
    logger.info("Training Random Forest Regressor model...")
    model = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
    model.fit(X_train, y_train)
    
    # 6. Evaluate Model on test set
    test_predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, test_predictions)
    rmse = np.sqrt(mean_squared_error(y_test, test_predictions))
    
    print("\nModel Evaluation Metrics (Test Set):")
    print(f"--> Mean Absolute Error (MAE): {round(mae, 2)} BRL")
    print(f"--> Root Mean Squared Error (RMSE): {round(rmse, 2)} BRL")
    print(f"--> Mean Weekly Sales: {round(y_test.mean(), 2)} BRL")
    
    # 7. Generate Future Forecast (Recursive multi-step forecast)
    forecast_inputs = weekly_sales.copy()
    future_forecast = []
    
    last_date = weekly_sales['purchase_date'].max()
    forecast_horizon = 8
    
    for i in range(forecast_horizon):
        next_date = last_date + pd.Timedelta(weeks=i+1)
        
        # Get lags from the end of the current forecast_inputs
        lag_1 = forecast_inputs.iloc[-1]['revenue']
        lag_2 = forecast_inputs.iloc[-2]['revenue']
        lag_3 = forecast_inputs.iloc[-3]['revenue']
        rolling_mean_4 = forecast_inputs.iloc[-4:]['revenue'].mean()
        
        # Predict next week
        X_pred = pd.DataFrame([{
            'lag_1': lag_1,
            'lag_2': lag_2,
            'lag_3': lag_3,
            'rolling_mean_4': rolling_mean_4
        }])
        pred_rev = model.predict(X_pred)[0]
        
        # Append prediction back so it acts as lag for subsequent predictions
        new_row = pd.DataFrame([{
            'purchase_date': next_date,
            'revenue': pred_rev,
            'lag_1': lag_1,
            'lag_2': lag_2,
            'lag_3': lag_3,
            'rolling_mean_4': rolling_mean_4
        }])
        forecast_inputs = pd.concat([forecast_inputs, new_row], ignore_index=True)
        
        future_forecast.append({
            'purchase_date': next_date,
            'forecasted_revenue': round(pred_rev, 2)
        })
        
    forecast_df = pd.DataFrame(future_forecast)
    print("\nFuture Weekly Sales Forecast (Next 8 Weeks):")
    print(forecast_df)
    
    # 8. Save output
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    csv_path = PROJECT_ROOT / "10_Reports" / "SQL_Reports"
    csv_path.mkdir(parents=True, exist_ok=True)
    forecast_df.to_csv(csv_path / "weekly_demand_forecast.csv", index=False)
    print(f"\nSaved forecast table to {csv_path / 'weekly_demand_forecast.csv'}")
    
    # 9. Plotting
    img_path = PROJECT_ROOT / "10_Reports" / "Dashboard"
    img_path.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(14, 7))
    sns.set_theme(style="whitegrid")
    
    # Plot historical actuals
    plt.plot(
        weekly_sales['purchase_date'], 
        weekly_sales['revenue'], 
        color='#34495e', 
        label='Historical Actuals', 
        linewidth=2
    )
    
    # Plot test predictions
    plt.plot(
        test_data['purchase_date'], 
        test_predictions, 
        color='#e74c3c', 
        linestyle='--', 
        marker='o', 
        label='Test Set Predictions', 
        linewidth=2
    )
    
    # Plot future forecast
    plt.plot(
        forecast_df['purchase_date'], 
        forecast_df['forecasted_revenue'], 
        color='#2ecc71', 
        linestyle=':', 
        marker='^', 
        label='8-Week Future Forecast', 
        linewidth=2.2
    )
    
    plt.title('AI Demand Forecasting: Weekly Sales (Revenue) Predictions', fontsize=15, fontweight='bold', pad=15)
    plt.xlabel('Date', fontsize=12, labelpad=12)
    plt.ylabel('Weekly Revenue (BRL)', fontsize=12, labelpad=12)
    plt.legend(loc='upper left', fontsize=11)
    
    plt.tight_layout()
    plt.savefig(img_path / "demand_forecast.png", dpi=300)
    plt.close()
    
    print(f"Saved forecast visual chart to {img_path / 'demand_forecast.png'}")
    logger.info("AI Demand Forecasting completed successfully.")

if __name__ == "__main__":
    run_demand_forecasting()
