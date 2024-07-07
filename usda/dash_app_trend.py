import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from statsmodels.tsa.seasonal import seasonal_decompose

# Load and preprocess dataset
def load_data(dataset_name):
    try:
        if dataset_name == 'Livestock':
            df = pd.read_csv("./livestock/psd_livestock.csv")
        elif dataset_name == 'Coffee':
            df = pd.read_csv("./coffee/psd_coffee.csv")
        elif dataset_name == 'Fruits':
            df = pd.read_csv("./fruits/psd_fruits_vegetables.csv")
        elif dataset_name == 'Grains':
            df = pd.read_csv("./grains/psd_grains_pulses.csv")
        else:
            df = pd.DataFrame()

        # Transform data using transform.Transform methods
        transformed_data = transform.Transform().transform_commodity_by_export(data=df)
        return transformed_data
    except Exception as e:
        print(f"Error loading and transforming data: {str(e)}")
        return pd.DataFrame()

# Analyze trends and turning points
def analyze_trends(df):
    results = seasonal_decompose(df['Value'], model='additive', period=1)
    df['Trend'] = results.trend
    df['Seasonal'] = results.seasonal
    df['Residual'] = results.resid
    return df

# Identify significant periods and generate summaries
def generate_summaries(df):
    summaries = []
    df['Change'] = df['Value'].pct_change()

    consistent_periods = df[df['Change'].abs() < 0.05]
    increasing_periods = df[df['Change'] > 0.05]
    decreasing_periods = df[df['Change'] < -0.05]

    summaries.append(f"Consistent periods: {consistent_periods['Calendar_Year'].min()} to {consistent_periods['Calendar_Year'].max()}")
    summaries.append(f"Increasing periods: {increasing_periods['Calendar_Year'].min()} to {increasing_periods['Calendar_Year'].max()}")
    summaries.append(f"Decreasing periods: {decreasing_periods['Calendar_Year'].min()} to {decreasing_periods['Calendar_Year'].max()}")

    highest_dropoff = df.loc[df['Drop_Off'].idxmax()]
    lowest_dropoff = df.loc[df['Drop_Off'].idxmin()]

    summaries.append(f"Highest drop-off in {highest_dropoff['Calendar_Year']} with a drop of {highest_dropoff['Drop_Off']}")
    summaries.append(f"Lowest drop-off in {lowest_dropoff['Calendar_Year']} with a drop of {lowest_dropoff['Drop_Off']}")

    return summaries

# Generate context based on analysis
def get_context_for_summaries(summaries):
    context = []
    for summary in summaries:
        # Placeholder for real context information
        context.append(f"{summary}. Potential reasons include economic factors, policy changes, and market conditions.")
    return context

# Main function to run the analysis
def main():
    dataset_name = 'Livestock'
    df = load_data(dataset_name)

    df = calculate_dropoffs(df)
    df = analyze_trends(df)

    summaries = generate_summaries(df)
    context = get_context_for_summaries(summaries)

    for c in context:
        print(c)

if __name__ == '__main__':
    main()
