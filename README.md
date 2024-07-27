# usda_viz
Visualize USDA data with LLM (i.e, ChatGPT 4) Summaries and Insights.

This visualization tool aggregates USDA commodities, and inserts the commodity name, minimum date, and maxiumum based on the zoom-in selection of the chart into ChatGPT 4. ChatGPT 4 proceeds to provide tailored insights and summaries based off the prompt.

The application is run using Streamlit to display the data, FastAPI to organize Python code, and ChatGPT 4 to process the LLM.

The first visual is a drop down menu of the USDA commodity data, and the commodity type:
<img width="1440" alt="Screenshot 2024-07-27 at 2 27 53 PM" src="https://github.com/user-attachments/assets/24d2f0c5-81ea-4fe3-bed5-d6de0ed65962">
