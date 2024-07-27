from openai import AsyncOpenAI
import streamlit as st
from config import OPENAI_API_KEY

async def get_chatgpt_insights(prompt):
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    except:
        client = AsyncOpenAI()
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )
        print("Response received.")  # Debugging statement
        async for chunk in response:
            if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    #print(f"delta.content received: {delta.content}")  # Debugging statement
                    yield delta.content
            else:
                print("No 'choices' attribute found in chunk or 'choices' is empty.")
    except Exception as e:
        print(f"Error in get_chatgpt_insights: {e}")  # Debugging statement
        raise e
