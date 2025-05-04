# chatbot.py
import streamlit as st
from typing import Dict, Any, List
import openai
import json
import decimal

class ChatBot:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.model = model
        openai.api_key = api_key
        self.client = openai.OpenAI(api_key=openai.api_key)
        

    def get_response(self, user_input: str, context: List[Dict[str, Any]]) -> str:
        """Generate a response using the database context."""

        def decimal_default(obj):
            if isinstance(obj, decimal.Decimal):
                return float(obj)
            raise TypeError

        context_json = json.dumps(context, indent=2, default=decimal_default)

        system_message = f"""
    You are a helpful assistant for a Worker Cost Calculator application.

    You have access to the following worker data:

    {context_json}

    When asked questions about workers, salaries, or worked hours, use this data to answer. 
    Always be factual. If data is missing, say you don’t have that information.
    Return concise but informative answers.
    """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content
