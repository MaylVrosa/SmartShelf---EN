# Imports
import pandas as pd
import numpy as np

# 1. LOADING THE DATA

# Load the CSVs (note: encoding? separator?)
products = pd.read_csv('data/products.csv')
monthly_summary = pd.read_csv('data/monthly_summary.csv')
seasonality_top = pd.read_csv('data/seasonality_top15.csv')
daily_sales = pd.read_csv('data/daily_sales_2021_2025.csv')
monthly_sales = pd.read_csv('data/monthly_sales_2021_2025.csv')
weekly_sales = pd.read_csv('data/weekly_sales_2021_2025.csv')

# 2. EXPLORATORY INSPECTION (run during development)

# Dictionary
all_data = {
    "products": products,
    "monthly_summary": monthly_summary,
    "seasonality_top": seasonality_top,
    "daily_sales": daily_sales,
    "monthly_sales": monthly_sales,
    "weekly_sales": weekly_sales,
}

# Loop kept as a comment: the code is done and was used for verification.
# Left commented out to avoid noisy output.
# for name, df in all_data.items():
    # print(f"===== {name} =====")
    # First 5 rows
    # print(df.head())
    # Check each one's info
    # df.info()
    # Describe each one
    # print(df.describe())
    # List how many unique values it has
    # print(df.nunique())
    # Check for duplicate rows
    # print(df.duplicated().sum())

# 3. CLEANING AND PREPARATION (daily_sales = source of truth)

# Check the date range (do the min and max make sense?)
min_date = daily_sales['date'].min()          # ← column
max_date = daily_sales['date'].max()          # ← column
print(f"date range: {min_date} to {max_date}")

# Convert 'date' from text to datetime (errors='coerce' -> invalid
# dates become NaT instead of crashing)
daily_sales['date'] = pd.to_datetime(daily_sales['date'], format='%Y-%m-%d', errors='coerce')  # ← column
print("Check for NaT in the data")
print(daily_sales['date'].isna().sum())       # ← column

# Extract year and month from the date (only possible because 'date' is already datetime)
daily_sales['year'] = daily_sales['date'].dt.year    # ← column
daily_sales['month'] = daily_sales['date'].dt.month  # ← column

# 4. MONTHLY AGGREGATION + VALIDATION AGAINST GROUND TRUTH

# Sum units sold per product x year x month
aggregation = daily_sales.groupby(["product_id", "year", "month"])["units"].sum().reset_index()  # ← column
print("Aggregation shape", aggregation.shape)

# Validate: compare my aggregation with the ready-made ground truth (monthly_sales)
validation = pd.merge(aggregation, monthly_sales, on=['product_id', 'year', 'month'])

# Difference between my sum (units_x) and the ground truth (units_y)
validation['difference'] = validation['units_x'] - validation['units_y']  # ← column

# Count diverging rows: if 0, the aggregation is correct
divergences = (validation['difference'] != 0).sum()
print(f"Diverging rows: {divergences}")

# 5. FULL GRID (fill months with no sales with 0)

# Unique values of each dimension
unique_products = aggregation["product_id"].unique()
unique_years = aggregation["year"].unique()
unique_months = aggregation["month"].unique()

# Turn each list into a mini-table for the cross join
df_products = pd.DataFrame({"product_id": unique_products})
df_years = pd.DataFrame({"year": unique_years})
df_months = pd.DataFrame({"month": unique_months})

# Grid = cartesian product (all possible combinations)
grid = df_products.merge(df_years, how="cross").merge(df_months, how="cross")
print(grid.shape)

# Fit the aggregation into the grid (how='left' keeps ALL grid rows)
result = grid.merge(aggregation, on=["product_id", "year", "month"], how="left")

# Months with no sales came as NaN; fill with 0
result["units"] = result["units"].fillna(0)  # ← column
print("Gaps filled (remaining NaN, should be 0):", result["units"].isna().sum())


# 6. FORECAST BY WEIGHTED AVERAGE (5 years)

# Pivot: one row per product x month, one column per year
pivot_table = result.pivot_table(
    index=["product_id", "month"],
    columns="year",
    values="units"                            # ← column
)

# Forecast = sum of each year x its weight
pivot_table["forecast"] = (
    pivot_table[2025] * 0.35
    + pivot_table[2024] * 0.25
    + pivot_table[2023] * 0.18
    + pivot_table[2022] * 0.12
    + pivot_table[2021] * 0.10
)

# 7. BACKTEST — validate the forecast quality (MAE and MAPE)

# Predict 2025 using ONLY 2021-2024 (weights renormalised to sum to 1)
pivot_table["forecast_2025"] = (
    pivot_table[2024] * 0.389
    + pivot_table[2023] * 0.277
    + pivot_table[2022] * 0.2
    + pivot_table[2021] * 0.133
)

# Absolute error of each row: |predicted - actual|
pivot_table["error"] = (pivot_table["forecast_2025"] - pivot_table[2025]).abs()

# MAE — mean error in units
mae = pivot_table["error"].mean()
print(f"MAE (mean absolute error): {mae}")

# MAPE — mean error in %. Exclude rows with actual=0 (no division by zero)
with_sales = pivot_table[pivot_table[2025] != 0]
total = len(pivot_table)
used = len(with_sales)
print(f"MAPE computed over {used} rows; {total - used} excluded (zero sales)")

mape = (with_sales["error"] / with_sales[2025]).mean() * 100
print(f"MAPE (mean percentage error): {mape:.1f}%")

# 8. ORDER FORMULA

# Clean table: only product, month and forecast
flat_table = pivot_table.reset_index()
product_forecasts = flat_table[["product_id", "month", "forecast"]]

# FICTITIOUS stock to test the formula; will come from the real count (manual/photo) later
product_forecasts["stock"] = np.random.randint(0, 60, size=len(product_forecasts))

# Apply the formula (forecast + 15% safety margin, minus the stock)
product_forecasts["order"] = product_forecasts["forecast"] * 1.15 - product_forecasts["stock"]

# Order is never negative (if there is spare stock, order nothing)
product_forecasts["order"] = product_forecasts["order"].clip(lower=0)

# 9. CONVERT INTO BOXES

# Bring in each product's box size
product_forecasts = product_forecasts.merge(
    products[["product_id", "units_per_box"]],  # ← column
    on="product_id",
    how="left"
)

# Number of boxes = order / box size, rounded up
product_forecasts["boxes_to_order"] = np.ceil(
    product_forecasts["order"] / product_forecasts["units_per_box"]  # ← column
)

# Actual units those boxes bring
product_forecasts["total_units"] = product_forecasts["boxes_to_order"] * product_forecasts["units_per_box"]  # ← column

# Bring in the product name (for the readable list)
product_forecasts = product_forecasts.merge(
    products[["product_id", "name"]],           # ← column
    on="product_id",
    how="left"
)

# 10. FINAL ORDER LIST

# Only products that need an order (boxes > 0)
final_order = product_forecasts[product_forecasts["boxes_to_order"] > 0]

for index, row in final_order.iterrows():
    print(f"{row['name']} (month {row['month']}): order {row['boxes_to_order']} box(es) = {row['total_units']} units")
