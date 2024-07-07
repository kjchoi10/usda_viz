import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
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
        transformed_data = transform.Transform().transform_commodity_by_country_export(data=df)
        return transformed_data
    except Exception as e:
        print(f"Error loading and transforming data: {str(e)}")
        return pd.DataFrame()

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
            id='country-dropdown',
            options=[{'label': country, 'value': country} for country in df['Country_Name'].unique()],
            value=df['Country_Name'].unique()[0],
            clearable=False
        ),
        dcc.Dropdown(
            id='commodity-dropdown',
            options=[{'label': commodity, 'value': commodity} for commodity in df['Commodity_Description'].unique()],
            value=df['Commodity_Description'].unique()[0],
            clearable=False
        ),
        dcc.Graph(id='bar-chart')
    ])

    @app.callback(
        [
            Output('country-dropdown', 'options'),
            Output('country-dropdown', 'value'),
            Output('commodity-dropdown', 'options'),
            Output('commodity-dropdown', 'value'),
            Output('bar-chart', 'figure')
        ],
        [
            Input('dataset-dropdown', 'value'),
            Input('country-dropdown', 'value'),
            Input('commodity-dropdown', 'value')
        ]
    )
    def update_chart(selected_dataset, selected_country, selected_commodity):
        try:
            df = load_data(selected_dataset)

            country_options = [{'label': country, 'value': country} for country in df['Country_Name'].unique()]
            commodity_options = [{'label': commodity, 'value': commodity} for commodity in df['Commodity_Description'].unique()]

            if selected_country is None:
                selected_country = df['Country_Name'].unique()[0]
            if selected_commodity is None:
                selected_commodity = df['Commodity_Description'].unique()[0]

            filtered_df = df[(df['Country_Name'] == selected_country) & (df['Commodity_Description'] == selected_commodity)]

            if filtered_df.empty:
                fig = px.bar(title=f'No data for {selected_country} in {selected_commodity}')
            else:
                fig = px.bar(filtered_df, x='Calendar_Year', y='Value', title=f'Values for {selected_country} in {selected_commodity}')
                fig.update_layout(xaxis_title='Calendar_Year', yaxis_title='Value')

            return country_options, selected_country, commodity_options, selected_commodity, fig
        except Exception as e:
            print(f"Error updating chart: {str(e)}")
            return [], None, [], None, {}

    return app

if __name__ == '__main__':
    app = create_dash_app()
    app.run_server(debug=True)
