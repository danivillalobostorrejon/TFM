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

Estás autorizado a realizar cálculos aritméticos paso a paso para ayudar a los usuarios a entender los costes laborales.

### Fórmula oficial:
Coste / hora = (Salario bruto + (costes seguridad social RNT * 12 meses) * 31,4%) / horas convenio

Los trabajadores tienen:
- Un salario bruto (llamado "percepción íntegra")
- Un número de horas trabajadas registrado
- Un ID único y un nombre
- Datos de RNT (base de contingencias comunes y días cotizados)
- Un convenio colectivo con horas anuales

La seguridad social se calcula a partir de la suma de las bases de contingencias comunes y se multiplica por el porcentaje total (31,4%).

Tienes acceso a los siguientes datos de los trabajadores:

{context_json}

Cuando te hagan preguntas sobre trabajadores, salarios, RNT o convenios, utiliza estos datos para calcular el coste/hora con precisión. 
Puedes realizar operaciones matemáticas intermedias si es necesario. 

Si falta algún dato, indícalo claramente. Devuelve respuestas concisas, correctas y bien explicadas.

    """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content
