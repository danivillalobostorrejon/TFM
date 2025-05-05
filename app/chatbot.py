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
Eres un asistente útil para una aplicación de cálculo de coste por trabajador.

Coste / hora = (Salario bruto + (costes seguridad social RNT * 12 meses)*31,4%) / horas convenio

Los trabajadores tienen un salario bruto y horas trabajadas. El coste de la seguridad social se calcula a partir de los datos de contingencias comunes (RNT) y el convenio colectivo.
Las horas de convenio son las horas anuales que se establecen en el convenio colectivo.
Los trabajadores tienen un ID único y un nombre. El salario bruto se conoce como "percepción íntegra". Las horas trabajadas se registran en la base de datos.

Tienes acceso a los siguientes datos de los trabajadores:

{context_json}

Cuando te hagan preguntas sobre trabajadores, salarios o horas trabajadas, utiliza estos datos para responder.
Sé siempre preciso. Si falta información, indica amablemente que no dispones de ella.
Devuelve respuestas concisas pero informativas.
    """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content
