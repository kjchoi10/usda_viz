import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import src.transform as transform

def create_dash_app():
    # Sample data loading function
    def load_data(dataset_name):
        if dataset_name == 'livestock':
            return transform.Transform().transform_commodity_by_all_export(data=transform.Transform().livestock)
        elif dataset_name == 'coffee':
            return transform.Transform().transform_commodity_by_all_export(data=transform.Transform().coffee)
        elif dataset_name == 'fruits':
            return transform.Transform().transform_commodity_by_all_export(data=transform.Transform().fruits)
        elif dataset_name == 'grains':
            return transform.Transform().transform_commodity_by_all_export(data=transform.Transform().grains)
        else:
            return pd.DataFrame()

    # Initial data load
    initial_dataset = 'livestock'
    df = load_data(initial_dataset)

    app = dash.Dash(__name__, requests_pathname_prefix='/dash/')

    app.layout = html.Div([
        dcc.Dropdown(
            id='dataset-dropdown',
            options=[
                {'label': 'Livestock', 'value': 'Livestock'},
                {'label': 'Coffee', 'value': 'Coffee'},
                {'label': 'Fruits', 'value': 'Fruits'},
                {'label': 'Grains', 'value': 'Grains'}
            ],
            value=initial_dataset,  # Default value
            clearable=False
        ),
        dcc.Dropdown(
            id='country-dropdown',
            options=[{'label': country, 'value': country} for country in df['Country_Name'].unique()],
            value=df['Country_Name'].unique()[0],  # Default value
            clearable=False
        ),
        dcc.Dropdown(
            id='commodity-dropdown',
            options=[{'label': year, 'value': year} for year in df['Calendar_Year'].unique()],
            value=df['Calendar_Year'].unique()[0],  # Default value
            clearable=False
        ),
        dcc.Graph(id='bar-chart')
    ])

    @app.callback(
        [Output('country-dropdown', 'options'),
         Output('country-dropdown', 'value'),
         Output('year-dropdown', 'options'),
         Output('year-dropdown', 'value'),
         Output('bar-chart', 'figure')],
        [Input('dataset-dropdown', 'value'),
         Input('country-dropdown', 'value'),
         Input('year-dropdown', 'value')]
    )
    def update_chart(selected_dataset, selected_country, selected_year):
        print(f"update_chart called with selected_dataset: {selected_dataset}, selected_country: {selected_country}, and selected_year: {selected_year}")
        
        # Load new data based on selected dataset
        df = load_data(selected_dataset)
        
        # Update country and year dropdown options
        country_options = [{'label': country, 'value': country} for country in df['Country_Name'].unique()]
        year_options = [{'label': year, 'value': year} for year in df['Calendar_Year'].unique()]

        # Set default values if none are selected
        if selected_country is None:
            selected_country = df['Country_Name'].unique()[0]
        if selected_year is None:
            selected_year = df['Calendar_Year'].unique()[0]

        # Filter data based on selections
        filtered_df = df[(df['Country_Name'] == selected_country) & (df['Calendar_Year'] == selected_year)]
        print(f"Filtered DataFrame:\n{filtered_df}")
        
        # Create figure
        if filtered_df.empty:
            fig = px.bar(title=f'No data for {selected_country} in {selected_year}')
        else:
            fig = px.bar(filtered_df, x='Calendar_Year', y='Value', title=f'Values for {selected_country} in {selected_year}')
            fig.update_layout(xaxis_title='Calendar_Year', yaxis_title='Value')
        
        return country_options, selected_country, year_options, selected_year, fig

    return app

if __name__ == '__main__':
    app = create_dash_app()
    app.run_server(debug=True)
