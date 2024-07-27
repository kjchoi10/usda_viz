# usda_viz
Visualize USDA data with LLM (i.e, ChatGPT 4) Summaries and Insights.

# Description:
This visualization tool aggregates USDA commodities, and inserts the commodity name, minimum date, and maxiumum based on the zoom-in selection of the chart into ChatGPT 4. ChatGPT 4 proceeds to provide tailored insights and summaries based off the prompt. An example of a prompt is: 
- prompts = {'starter': 
"Given the commodity related to {selected_commodity}, can you provide me the top five insights or trends between the dates {x_min} to {x_max} about the commodity as USA export with references? Please provide specific dates if you've provided any updates on outbreaks, trade agreements, globalization trends, or economic research. It's fine to add sub-bullet points. Please remove any note about being an AI agent in your response."}

# Technical Stack:
- The application is run using Streamlit to display the data, FastAPI to organize Python code, and ChatGPT 4 to process the LLM.

#### First Visual:
- The first visual is a drop down menu of the USDA commodity data, and the commodity type:
<img width="1440" alt="Screenshot 2024-07-27 at 2 27 53 PM" src="https://github.com/user-attachments/assets/24d2f0c5-81ea-4fe3-bed5-d6de0ed65962">

#### Second Visual:
- The second visual is activated once the submit button is clicked on. It provides a bar chart of the commodity with a three-year moving average. Instantly afterwards though the commodity, minimum and maximum date are sent to ChatGPT4 to process a summary text.
<img width="1440" alt="Screenshot 2024-07-27 at 2 30 58 PM" src="https://github.com/user-attachments/assets/191d4e03-607d-4ac2-9b4c-e7a79680c7b5">

#### Third Visual:
- The third visual is the ChatGPT 4 summary text:
<img width="1440" alt="Screenshot 2024-07-27 at 2 31 34 PM" src="https://github.com/user-attachments/assets/1ff72b9b-9741-42ff-8709-29efed698367">


