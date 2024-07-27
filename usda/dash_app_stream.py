import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from chatgpt_handler import get_chatgpt_insights
import transform
import asyncio

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
        st.error(f"Error loading and transforming data: {str(e)}")
        return pd.DataFrame()

async def fetch_insights(prompt, placeholder, debug_placeholder):
    insights = ""
    try:
        async for chunk in get_chatgpt_insights(prompt):
            #st.write(f"Debug chunk: {chunk}")  # Debug output in Streamlit app
            if chunk.strip() == "[DONE]":
                continue  # Ignore the [DONE] chunk 
            insights += chunk
            #debug_placeholder.write(f"Received chunk: {chunk}")  # Logging each chunk for debugging
            placeholder.markdown(f"* {insights.strip()}")
    except Exception as e:
        st.error(f"Error fetching insights: {str(e)}")

def main():
    st.title("Commodity Insights")

    dataset_options = ['Livestock', 'Coffee', 'Fruits', 'Grains']
    dataset = st.selectbox("Select Dataset", dataset_options)
    
    df = load_data(dataset)
    commodities = df['Commodity_Description'].unique().tolist()
    commodity = st.selectbox("Select Commodity", commodities)
    
    if st.button("Submit"):
        filtered_df = df[df['Commodity_Description'] == commodity]
        
        if not filtered_df.empty:
            fig = px.bar(filtered_df, x='Calendar_Year', y='Value', title=f'Values for {commodity}')
            # Customize the width and height of the figure
            fig.update_layout(
                autosize=False,
                width=1000,  # Set the width of the figure
                height=600,  # Set the height of the figure
                xaxis_title='Calendar Year',
                yaxis_title='Value'
            )
            
            filtered_df['Moving_Avg'] = filtered_df['Value'].rolling(window=3).mean()
            
            fig.add_trace(go.Scatter(
                x=filtered_df['Calendar_Year'],
                y=filtered_df['Moving_Avg'],
                mode='lines',
                name='3-Year Moving Avg',
                line=dict(color='orange')
            ))
            
            st.plotly_chart(fig, use_container_width=False, config={'responsive': False}) 

        prompt = f"Given the commodity related to {commodity}, can you provide me the top five insights or trends about the commodity as USA export with references? Please remove any AI apparent conversations, and only provide the prompt response."
        
        placeholder = st.empty()
        debug_placeholder = st.empty()
        with st.spinner('Fetching insights...'):
            asyncio.run(fetch_insights(prompt, placeholder, debug_placeholder))

if __name__ == "__main__":
    main()
