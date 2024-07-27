import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import transform
import asyncio
from chatgpt_handler_ import get_chatgpt_insights  # Import the function from the other script

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
    
# older version for sync with all outputs not chunks
def format_insights_as_markdown_(insights):
    # Ensure each insight starts with a new line and a bullet point
    insights_lines = insights.split('\n')
    formatted_lines = []
    for line in insights_lines:
        if line.strip():
            if not line.startswith("* "):
                formatted_lines.append(f"* {line.strip()}")
            else:
                formatted_lines.append(line.strip())
    return "\n".join(formatted_lines)

def format_insights_as_markdown(insights):
    insights_lines = insights.split('\n')
    bullet_points = []
    for line in insights_lines:
        if line.strip():
            bullet_points.append(f"* {line.strip()}")
    return "\n".join(bullet_points)

async def stream_insights(prompt, update_callback):
    insights = ""
    async for chunk in get_chatgpt_insights(prompt):
        insights += chunk
        formatted_insights = format_insights_as_markdown(insights)
        update_callback(dcc.Markdown(formatted_insights))

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
            #print(f"Commodity options: {commodity_options}")

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
        Output('summary-output', 'children')
        ],
        [Input('bar-chart', 'relayoutData')],
        [State('dataset-dropdown', 'value'), State('commodity-dropdown', 'value')]
    )
    async def display_summaries(relayoutData, selected_dataset, selected_commodity):
        if not relayoutData or 'xaxis.range[0]' not in relayoutData or 'xaxis.range[1]' not in relayoutData:
            return ["Zoom in on the chart to see the data, and auto-generate a summary."]
        
        async def update_summary_output(prompt):
            try:
                await stream_insights(prompt, lambda insights: app.callback_context.triggered[0]['value'] == insights)
            except Exception as e:
                return [f"Error fetching insights from ChatGPT: {str(e)}"]
            
        try:
            df = load_data(selected_dataset)
            df = df[df['Commodity_Description'] == selected_commodity]

            x_min = int(relayoutData['xaxis.range[0]'])
            x_max = int(relayoutData['xaxis.range[1]'])

            df = df[(df['Calendar_Year'] >= x_min) & (df['Calendar_Year'] <= x_max)]

            # Prepare the list of selected years and values
            selected_years_text = ", ".join(f"{row['Calendar_Year']}: {row['Value']}" for _, row in df.iterrows())

            # Generate the ChatGPT prompt
            # Future Prompt: "For context, the selected years and values (i.e, in metric tons) are: {selected_years_text}"
            chatgpt_prompt = f"Given the commodity related to {selected_commodity}, can you provide me the top five insights or trends between the dates {x_min} to {x_max} about the commodity as USA export with references? Please provide specific dates if you've provided any updates on outbreaks, trade agreements, globlization trends, or economic research. It's fine to add sub-bullet points. Please remove any note about being an AI agent in your response."
            # Get insights from ChatGPT
            #insights = asyncio.run(get_insights(chatgpt_prompt))
            #print('insights: ', insights)
            #formatted_insights = format_insights_as_markdown(insights)
            #return next(get_and_display_insights(chatgpt_prompt))
            asyncio.run(update_summary_output(chatgpt_prompt))

        except Exception as e:
            return [f"Error displaying data: {str(e)}"]

    return app

if __name__ == '__main__':
    app = create_dash_app()
    app.run_server(debug=True)
