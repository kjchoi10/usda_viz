import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
import transform

def load_data(dataset_name):
    try:
        # Load data locally
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

def calculate_dropoffs(df):
    df['Previous_Year_Value'] = df.groupby('Commodity_Description')['Value'].shift(1)
    df['Drop_Off'] = df['Previous_Year_Value'] - df['Value']
    df['Year_Over_Year_Change'] = (df['Drop_Off'] / df['Previous_Year_Value']) * 100
    return df

def get_top_dropoff_years(df, top_n=3):
    dropoff_df = df.nlargest(top_n, 'Drop_Off')
    return dropoff_df[['Calendar_Year', 'Drop_Off']]

def analyze_trends(df):
    results = seasonal_decompose(df['Value'], model='additive', period=1)
    df['Trend'] = results.trend
    df['Seasonal'] = results.seasonal
    df['Residual'] = results.resid
    return df

def detect_changepoints(values, threshold=0.1):
    """
    Simulated changepoint detection based on significant percentage changes in values.
    """
    changepoints = []
    for i in range(1, len(values)):
        percent_change = abs((values[i] - values[i - 1]) / values[i - 1])
        if percent_change > threshold:
            changepoints.append(i)
    return changepoints

def generate_decade_summaries(df):
    summaries = []
    decades = df['Calendar_Year'].astype(str).apply(lambda x: x[:4]).unique()
    for decade in decades:
        decade_data = df[df['Calendar_Year'].astype(str).str.startswith(decade)]
        if not decade_data.empty:
            max_value = decade_data['Value'].max()
            min_value = decade_data['Value'].min()
            decade_summary = f"{decade}: Max Value = {max_value}, Min Value = {min_value}"
            summaries.append(decade_summary)

    return summaries

def generate_summaries(df):
    summaries = []
    df['Change'] = df['Value'].pct_change()

    # Detect significant changepoints
    values = df['Value'].tolist()
    changepoints = detect_changepoints(values, threshold=0.1)
    if changepoints:
        summaries.append(f"Significant changepoints detected at years: {', '.join(str(df.iloc[idx]['Calendar_Year']) for idx in changepoints)}")

    # Generate decade-based summaries
    decade_summaries = generate_decade_summaries(df)
    if decade_summaries:
        summaries.append("Decade summaries:")
        summaries.extend(decade_summaries)

    highest_dropoff = df.loc[df['Drop_Off'].idxmax()]
    lowest_dropoff = df.loc[df['Drop_Off'].idxmin()]

    summaries.append(f"Highest drop-off in {highest_dropoff['Calendar_Year']} with a drop of {highest_dropoff['Drop_Off']}")
    summaries.append(f"Lowest drop-off in {lowest_dropoff['Calendar_Year']} with a drop of {lowest_dropoff['Drop_Off']}")

    return summaries

def get_context_for_year(year, highest_value, highest_value_year, lowest_value, lowest_value_year):
    try:
        # Here you would normally fetch the context data from an external API or database.
        # For simplicity, we will return a static message.
        return (f"In {year}, USA cattle exports experienced a significant drop-off. "
                f"The highest value in the selected range was {highest_value} in {highest_value_year}, and the lowest value was {lowest_value} in {lowest_value_year}. "
                "This could be due to multiple factors including economic downturns, changes in trade policies, and disease outbreaks affecting livestock.")
    except Exception as e:
        print(f"Error fetching context for year {year}: {str(e)}")
        return "Error fetching context for the year."

def get_context_for_summaries(summaries):
    try:
        context_messages = []

        for summary in summaries:
            print('summary: ', summary)
            if summary.startswith("Highest drop-off"):
                context_messages.append("The highest drop-off reflects a significant decrease in values for a specific year.")
            elif summary.startswith("Lowest drop-off"):
                context_messages.append("The lowest drop-off represents the least decrease in values observed.")
            else:
                context_messages.append("Additional context could be provided here based on specific summaries.")

        return context_messages
    except Exception as e:
        print(f"Error fetching context for summaries: {str(e)}")
        return ["Error fetching context for summaries."]

def create_dash_app():
    initial_dataset = 'Livestock'
    df = load_data(initial_dataset)

    app = dash.Dash(__name__)
    app.layout = html.Div([
        dcc.Dropdown(
            id='dataset-dropdown',
            options=[
                {'label': 'Livestock', 'value': 'Livestock'},
                {'label': 'Coffee', 'value': 'Coffee'},
                {'label': 'Fruits', 'value': 'Fruits'},
                {'label': 'Grains', 'value': 'Grains'}
            ],
            value=initial_dataset,
            clearable=False
        ),
        dcc.Dropdown(
            id='commodity-dropdown',
            options=[{'label': commodity, 'value': commodity} for commodity in df['Commodity_Description'].unique()],
            value=df['Commodity_Description'].unique()[0],
            clearable=False
        ),
        dcc.Graph(id='bar-chart'),
        html.Div(id='dropoff-output'),
        html.Div(id='summary-output')
    ])

    @app.callback(
        [
            Output('commodity-dropdown', 'options'),
            Output('commodity-dropdown', 'value'),
            Output('bar-chart', 'figure')
        ],
        [
            Input('dataset-dropdown', 'value'),
            Input('commodity-dropdown', 'value')
        ]
    )
    def update_chart(selected_dataset, selected_commodity):
        try:
            df = load_data(selected_dataset)
            print(f"Loaded data for dataset '{selected_dataset}'. Shape: {df.shape}")

            commodity_options = [{'label': commodity, 'value': commodity} for commodity in df['Commodity_Description'].unique()]
            print(f"Commodity options: {commodity_options}")

            if selected_commodity is None:
                selected_commodity = df['Commodity_Description'].unique()[0]
                print(f"Selected commodity defaulted to: {selected_commodity}")

            filtered_df = df[df['Commodity_Description'] == selected_commodity]

            if filtered_df.empty:
                fig = px.bar(title=f'No data for {selected_commodity}')
            else:
                fig = px.bar(filtered_df, x='Calendar_Year', y='Value', title=f'Values for {selected_commodity}')
                fig.update_layout(xaxis_title='Calendar_Year', yaxis_title='Value')

                # Calculate moving average
                filtered_df = filtered_df.sort_values('Calendar_Year')
                filtered_df['Moving_Avg'] = filtered_df['Value'].rolling(window=3).mean()

                # Add moving average line to the chart
                fig.add_trace(go.Scatter(
                    x=filtered_df['Calendar_Year'],
                    y=filtered_df['Moving_Avg'],
                    mode='lines',
                    name='3-Year Moving Avg',
                    line=dict(color='orange')
                ))

            return commodity_options, selected_commodity, fig
        except Exception as e:
            print(f"Error updating chart: {str(e)}")
            return [], None, {}

    @app.callback(
        [
            Output('dropoff-output', 'children'),
            Output('summary-output', 'children')
        ],
        [Input('bar-chart', 'relayoutData')],
        [State('dataset-dropdown', 'value'), State('commodity-dropdown', 'value')]
    )
    def display_summaries(relayoutData, selected_dataset, selected_commodity):
        if not relayoutData or 'xaxis.range[0]' not in relayoutData or 'xaxis.range[1]' not in relayoutData:
            return "Zoom in on the chart to see the drop-offs.", "Zoom in on the chart to see the summaries."

        try:
            df = load_data(selected_dataset)
            df = df[df['Commodity_Description'] == selected_commodity]

            x_min = relayoutData['xaxis.range[0]']
            x_max = relayoutData['xaxis.range[1]']

            df = df[(df['Calendar_Year'] >= x_min) & (df['Calendar_Year'] <= x_max)]
            df = calculate_dropoffs(df)
            df = analyze_trends(df)
            top_dropoffs = get_top_dropoff_years(df, top_n=1)

            if top_dropoffs.empty:
                return "No significant drop-offs found.", "No significant summaries found."

            highest_dropoff_year = top_dropoffs.iloc[0]['Calendar_Year']
            highest_value_row = df.loc[df['Value'].idxmax()]
            highest_value = highest_value_row['Value']
            highest_value_year = highest_value_row['Calendar_Year']

            lowest_value_row = df.loc[df['Value'].idxmin()]
            lowest_value = lowest_value_row['Value']
            lowest_value_year = lowest_value_row['Calendar_Year']

            context = get_context_for_year(highest_dropoff_year, highest_value, highest_value_year, lowest_value, lowest_value_year)
            top_dropoffs_text = ", ".join(f"{row['Calendar_Year']} ({row['Drop_Off']})" for _, row in top_dropoffs.iterrows())
            summaries = generate_summaries(df)
            context_summaries = get_context_for_summaries(summaries)
            summary_text = " ".join(context_summaries)

            return f"The highest drop-offs are: {top_dropoffs_text}. {context}", summary_text
        except Exception as e:
            print(f"Error displaying drop-offs: {str(e)}")
            return "Error displaying drop-offs.", "Error displaying summaries."
        
    return app

if __name__ == '__main__':
    app = create_dash_app()
    app.run_server(debug=True)
