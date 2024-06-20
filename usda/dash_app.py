import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import transform

def create_dash_app():
    # Sample data
    df = transform.Transform().transform_commodity_by_country_export(data=transform.Transform().livestock, commodity='Meat, Chicken')

    app = dash.Dash(__name__, requests_pathname_prefix='/dash/')

    app.layout = html.Div([
        dcc.Dropdown(
            id='category-dropdown',
            options=[{'label': category, 'value': category} for category in df['Country_Name'].unique()],
            value=df['Country_Name'].unique()[0],  # Default value
            clearable=False
        ),
        dcc.Graph(id='bar-chart')
    ])

    @app.callback(
        Output('bar-chart', 'figure'),
        Input('category-dropdown', 'value')
    )
    def update_chart(selected_category):
        print(f"update_chart called with selected_category: {selected_category}")
        if selected_category is None:
            print("No category selected")
            return {}
        filtered_df = df[df['Country_Name'] == selected_category]
        print(f"Filtered DataFrame:\n{filtered_df}")
        if filtered_df.empty:
            print("Filtered DataFrame is empty")
            return {}
        fig = px.bar(filtered_df, x='Calendar_Year', y='Value', title=f'Values for Category {selected_category}')
        fig.update_layout(xaxis_title='Calendar_Year', yaxis_title='Value')
        return fig

    return app
