import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import numpy as np
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

def get_context_for_summaries(summaries):
    context = []
    for summary in summaries:
        # Placeholder for real context information
        context.append(f"{summary}. Potential reasons include economic factors, policy changes, and market conditions.")
    return context

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

def create_dash_app():
    initial_dataset = 'Livestock'
    df = load_data(initial_dataset)

    app = dash.Dash(__name__)
    print('app: ', app)
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

            commodity_options = [{'label': commodity, 'value': commodity} for commodity in df['Commodity_Description'].unique()]

            if selected_commodity is None:
                selected_commodity = df['Commodity_Description'].unique()[0]

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
