import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import transform
from flask import Flask, Response, stream_with_context, request
import asyncio
from chatgpt_handler import get_chatgpt_insights

# Set up Flask server for streaming
server = Flask(__name__)

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

        transformed_data = transform.Transform().transform_commodity_by_export(data=df)
        return transformed_data
    except Exception as e:
        print(f"Error loading and transforming data: {str(e)}")
        return pd.DataFrame()

def format_insights_as_markdown(insights):
    insights_lines = insights.split('\n')
    bullet_points = [f"* {line.strip()}" for line in insights_lines if line.strip()]
    return "\n".join(bullet_points)

async def stream_insights(prompt):
    insights = ""
    async for chunk in get_chatgpt_insights(prompt):
        print('chunk from stream_insights: ', chunk)
        insights += chunk
        formatted_insights = format_insights_as_markdown(insights)
        yield f"data: {formatted_insights}\n\n"

@server.route('/stream_insights')
def stream_insights_route():
    prompt = request.args.get('prompt')
    print('prompt: ', prompt)
    async def generate():
        async for chunk in stream_insights(prompt):
            print('chunk: ', chunk )
            yield chunk
    return Response(stream_with_context(generate()), content_type='text/event-stream')

def create_dash_app():
    app = dash.Dash(__name__, server=server, suppress_callback_exceptions=True)
    initial_dataset = 'Livestock'
    df = load_data(initial_dataset)

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
        html.Div(id='summary-output'),
        dcc.Interval(id='interval-component', interval=1000, n_intervals=0),
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

            if selected_commodity is None:
                selected_commodity = df['Commodity_Description'].unique()[0]

            filtered_df = df[df['Commodity_Description'] == selected_commodity]

            if filtered_df.empty:
                fig = px.bar(title=f'No data for {selected_commodity}')
            else:
                fig = px.bar(filtered_df, x='Calendar_Year', y='Value', title=f'Values for {selected_commodity}')
                fig.update_layout(xaxis_title='Calendar_Year', yaxis_title='Value')

                filtered_df['Moving_Avg'] = filtered_df['Value'].rolling(window=3).mean()

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
        Output('summary-output', 'children'),
        [Input('bar-chart', 'relayoutData')],
        [State('dataset-dropdown', 'value'), State('commodity-dropdown', 'value')]
    )
    async def display_summaries(relayoutData, selected_dataset, selected_commodity):
        if not relayoutData or 'xaxis.range[0]' not in relayoutData or 'xaxis.range[1]' not in relayoutData:
            return "Zoom in on the chart to see the data, and auto-generate a summary."
        
        async def get_and_display_insights(prompt):
            insights = ""
            try:
                async for chunk in get_chatgpt_insights(prompt):
                    insights += chunk
                    formatted_insights = format_insights_as_markdown(insights)
                    yield formatted_insights
            except Exception as e:
                yield f"Error fetching insights from ChatGPT: {str(e)}"

        try:
            df = load_data(selected_dataset)
            df = df[df['Commodity_Description'] == selected_commodity]

            x_min = int(relayoutData['xaxis.range[0]'])
            x_max = int(relayoutData['xaxis.range[1]'])

            df = df[(df['Calendar_Year'] >= x_min) & (df['Calendar_Year'] <= x_max)]

            selected_years_text = ", ".join(f"{row['Calendar_Year']}: {row['Value']}" for _, row in df.iterrows())
            chatgpt_prompt = f"Given the commodity related to {selected_commodity}, can you provide me the top five insights or trends between the dates {x_min} to {x_max} about the commodity as USA export with references? Please provide specific dates if you've provided any updates on outbreaks, trade agreements, globalization trends, or economic research. It's fine to add sub-bullet points. Please remove any note about being an AI agent in your response."

            return [dcc.Markdown(content=await get_and_display_insights(chatgpt_prompt))]
            #return next(get_and_display_insights(chatgpt_prompt))
        except Exception as e:
            print(f"Error displaying data: {str(e)}")
            return [f"Error fetching insights from ChatGPT: {str(e)}"]

    return app

if __name__ == '__main__':
    app = create_dash_app()
    app.run_server(debug=True)
