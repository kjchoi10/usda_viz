from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from chatgpt_handler import get_chatgpt_insights
import transform
import asyncio
import json

app = FastAPI()
templates = Jinja2Templates(directory="templates")

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
        try:
            chunk_data = json.loads(chunk)
            if "choices" in chunk_data:
                delta = chunk_data["choices"][0]["delta"]
                if "content" in delta:
                    insights += delta["content"]
                    if insights.endswith(".") or insights.endswith("!") or insights.endswith("?"):  # Assuming sentences end with these punctuations
                        formatted_insight = f"* {insights.strip()}"
                        insights = ""
                        yield f"data: {formatted_insight}\n\n"
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")


@app.get('/stream_insights')
async def stream_insights_route(request: Request):
    prompt = request.query_params.get('prompt')
    async def event_generator():
        async for chunk in stream_insights(prompt):
            yield chunk
    return StreamingResponse(event_generator(), media_type='text/event-stream')

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    df = load_data('Livestock')
    datasets = ['Livestock', 'Coffee', 'Fruits', 'Grains']
    commodities = df['Commodity_Description'].unique().tolist()
    return templates.TemplateResponse("index.html", {"request": request, "datasets": datasets, "commodities": commodities})

@app.get("/get_commodities")
async def get_commodities(dataset: str):
    df = load_data(dataset)
    commodities = df['Commodity_Description'].unique().tolist()
    return JSONResponse(content={"commodities": commodities})

@app.get("/get_chart")
async def get_chart(dataset: str, commodity: str):
    df = load_data(dataset)
    filtered_df = df[df['Commodity_Description'] == commodity]
    
    if filtered_df.empty:
        fig = px.bar(title=f'No data for {commodity}')
    else:
        fig = px.bar(filtered_df, x='Calendar_Year', y='Value', title=f'Values for {commodity}')
        fig.update_layout(xaxis_title='Calendar_Year', yaxis_title='Value')

        filtered_df['Moving_Avg'] = filtered_df['Value'].rolling(window=3).mean()

        fig.add_trace(go.Scatter(
            x=filtered_df['Calendar_Year'],
            y=filtered_df['Moving_Avg'],
            mode='lines',
            name='3-Year Moving Avg',
            line=dict(color='orange')
        ))

    graph_html = fig.to_html(full_html=False)
    return {"graph_html": graph_html}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
