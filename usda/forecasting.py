import pandas as pd
from prophet import Prophet
import transform

class Forecast():

    def __init__():
        return
    
    def default_data():
        """
        Description: Default data for testing purposes. Uses the commodity description 'Animial Number, Cattle'.
        Args: None
        Return:
            df: Pandas dataframe for the cattle dataset using the transform class.
        """
        # Load your data
        df = data=transform.Transform().livestock
        df = df[df['Commodity_Description'] == 'Animal Numbers, Cattle']
        df = transform.Transform().transform_commodity_by_export(data=df)
        return(df)
    
    def forecast(df):
        """
        Description: Using prophet we are going to create a forecast model.
        Args:
            df: Pandas dataset with specified commodity.
        Return:
            df: Pandas with forecast data.
        """
        # Rename columns to fit Prophet's requirements
        df.rename(columns={'Calendar_Year': 'ds', 'Value': 'y'}, inplace=True)
        # Ensure the date column is parsed as yearly data
        df['ds'] = pd.to_datetime(df['ds'], format='%Y')

        # Initialize and fit the Prophet model
        model = Prophet()
        model.fit(df)

        # Create a DataFrame for future dates (including historical dates)
        future = model.make_future_dataframe(periods=0, freq='Y')

        # Make predictions
        forecast = model.predict(future)

        # Extract the trend component
        trend = forecast[['ds', 'trend']]

        # Ensure proper alignment
        df = df.merge(trend, on='ds', how='left')
        return(df)
    
    def calculate_trend(df):
        """
        Description: Calculates low, medium, and high volatility + trend direction (i.e, None, decreas, increase).
        Args:
            df: Pandas forecast data using the forecast() function.
        Return:
            analysis_results: Combined dataset with trend and volatility.
            volatility_periods: Volatility dataset.
        """
        # Calculate the first derivative of the trend
        df['trend_diff'] = df['trend'].diff()

        # Identify periods of increase or decrease
        df['trend_direction'] = df['trend_diff'].apply(lambda x: 'Increase' if x > 0 else 'Decrease' if x < 0 else 'No Change')

        # Identify consecutive periods of increase or decrease
        trend_periods = df.groupby((df['trend_direction'] != df['trend_direction'].shift()).cumsum()).agg({
            'ds': ['first', 'last'],
            'trend_direction': 'first'
        }).reset_index(drop=True)
        # Rename columns
        trend_periods.columns = ['Start', 'End', 'Direction']
        return(trend_periods)

    def calculate_volatility(df):
        """
        Description: Calculates low, medium, and high volatility.
        Args:
            df: Pandas forecast data using the forecast() function.
        Return:
            volatility_periods: Volatility dataset.
        """
        # Calculate residuals
        df['residual'] = df['y'] - df['trend']

        # Calculate rolling standard deviation of residuals to assess volatility
        df['rolling_std'] = df['residual'].rolling(window=3, min_periods=1).std()  # 3-year rolling window with minimum periods

        # Define thresholds for high and low volatility
        high_volatility_threshold = df['rolling_std'].quantile(0.75)  # 75th percentile
        low_volatility_threshold = df['rolling_std'].quantile(0.25)   # 25th percentile

        # Identify periods of high and low volatility
        df['volatility'] = df['rolling_std'].apply(lambda x: 'High' if x > high_volatility_threshold else 'Low' if x < low_volatility_threshold else 'Medium')

        # Identify consecutive periods of high or low volatility
        volatility_periods = df.groupby((df['volatility'] != df['volatility'].shift()).cumsum()).agg({
            'ds': ['first', 'last'],
            'volatility': 'first'
        }).reset_index(drop=True)

        # Rename columns
        volatility_periods.columns = ['Start', 'End', 'Volatility']
        return(volatility_periods)

    def plot_trend_and_volatility(df, volatility_periods):
        """
        Description: Plots the trend and volatility periods with highlighted low, medium, and low volatility periods.
        Args:
            df: Pandas forecast dataset from the forecast() function.
            volatility_periods: Pandas dataset from the calculate_volatilty() function.
        Return:
            Plots the volatility periods.
        """
        import matplotlib.pyplot as plt
        # Plot original data with trend and volatility periods
        plt.figure(figsize=(12, 8))
        plt.plot(df['ds'], df['y'], label='Original Data')
        plt.plot(df['ds'], df['trend'], label='Trend', color='red')

        # Highlight periods of high, medium, and low volatility
        for _, row in volatility_periods.iterrows():
            plt.axvspan(row['Start'], row['End'], color='yellow' if row['Volatility'] == 'Medium' else 'red' if row['Volatility'] == 'High' else 'green', alpha=0.3)

        plt.legend()
        plt.title('Original Data with Trend and Volatility Periods')
        plt.show()
