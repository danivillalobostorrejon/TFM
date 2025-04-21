# chatbot.py
import streamlit as st
from typing import Dict, Any, List
import openai
import json

class ChatBot:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.model = model
        openai.api_key = api_key
        
    def get_response(self, user_input: str, context: Dict[str, Any]) -> str:
        """Generate a response to the user's query."""
        worker_data = json.dumps(context)
        
        system_message = f"""
        You are a helpful assistant for a Worker Cost Calculator application.
        You have access to the following worker data:
        {worker_data}
        
        When asked questions about workers, costs, or hours, use this data to provide accurate answers.
        If you're asked something you don't have data for, politely explain that you don't have that information.
        """
        
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input}
            ]
        )
        
        return response.choices[0].message.content
