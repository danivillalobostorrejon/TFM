import re
import openai
import json
from typing import Dict, Any

class LLMClassifier:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.model = model
        openai.api_key = api_key
        self.client = openai.OpenAI(api_key=openai.api_key)

    def classify_document_type(self, text: str) -> str:
        text_lower = text.lower()

        if "modelo 190" in text_lower or "percepción íntegra" in text_lower:
            return "modelo_190"
        elif "documento 10t" in text_lower or "rendimiento a integrar" in text_lower:
            return "10t"
        elif "rnt" in text_lower or "base de contingencias comunes" in text_lower:
            return "rnt"
        elif "tipos de cotización" in text_lower or "contingencias profesionales" in text_lower:
            return "idc"
        elif "convenio" in text_lower and "jornada" in text_lower and "horas" in text_lower:
            return "convenio"
        else:
            return "desconocido"

    def extract_structured_data(self, text: str) -> Dict[str, Any]:
        doc_type = self.classify_document_type(text)

        if doc_type == "modelo_190":
            return self.extract_from_modelo_190(text)
        elif doc_type == "10t":
            return self.extract_from_10t(text)
        elif doc_type == "rnt":
            raise ValueError("RNT necesita siglas del trabajador para extraer los datos.")
        elif doc_type == "idc":
            return self.extract_from_idc(text)
        elif doc_type == "convenio":
            return self.extract_from_convenio(text)
        else:
            raise ValueError("No se pudo clasificar el tipo de documento.")

    def _query_openai(self, prompt: str, doc_type: str = None) -> Dict[str, Any]:
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente experto en analizar documentos laborales y fiscales."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content.strip()
        # print(content)

        if doc_type == "modelo_190":
            match = re.search(r"\{.*\}", content, re.DOTALL)
        elif doc_type == "rnt":
            match = re.search(r"\[\s*\{.*?\}\s*(,\s*\{.*?\}\s*)*\]", content, re.DOTALL)

        if not match:
            raise ValueError("No se encontró ningún JSON válido en la respuesta del modelo.")

        json_text = match.group()

        # Normalizar números europeos: 272.904,14 -> 272904.14
        json_text = re.sub(r'(\d+)\.(\d{3}),(\d+)', r'\1\2.\3', json_text)  # 272.904,14 -> 272904.14
        json_text = re.sub(r'(\d+),(\d+)', r'\1.\2', json_text)  # 24214,44 -> 24214.44

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al parsear JSON: {e}\nContenido:\n{json_text}")

    def extract_from_modelo_190(self, text: str) -> Dict[str, Any]:
        prompt = f"""
Eres un asistente que extrae información fiscal de documentos PDF.
Tu tarea es encontrar el valor del campo \"Percepción íntegra\" asociado a un trabajador y devolverlo como JSON.
Ejemplo de salida:
{{"worker_name": "Jose Garcia Fontecha", "percepcion_integra": 24214.44}}

Contenido del documento:
{text}
"""
        return self._query_openai(prompt, "modelo_190")

    def extract_from_10t(self, text: str) -> Dict[str, Any]:
        prompt = f"""
Eres un asistente que extrae información fiscal de documentos PDF.
Tu tarea es encontrar el valor del campo \"Rendimiento a integrar\" asociado a un trabajador y devolverlo como JSON.
Ejemplo de salida:
{{ "rendimientos": [{{"nombre": "Jose Garcia Fontecha", "rendimiento_integrar": 60000.00}}] }}

Contenido del documento:
{text}
"""
        return self._query_openai(prompt)

    def extract_from_rnt(self, text: str) -> str:
        prompt = f"""
    Eres un asistente que extrae información de documentos RNT mensuales de la Seguridad Social.

    Tu tarea es:

    1. Leer el texto y devolver una lista de trabajadores, donde cada uno tiene:
        - `"siglas"`: el identificador del trabajador (CAF), de 5 letras mayúsculas.
        - `"base_contingencias_comunes"`: número decimal, por ejemplo: 3170.19
        - `"dias_cotizados"`: número entero, por ejemplo: 30

    2. Extraer también el **periodo de liquidación** del documento. Aparece como:
    `"Periodo de liquidación 12/2021-12/2021"`
    Interprétalo y devuelve el valor `"01-12-2021"` (día 1 del mes indicado).

    El resultado debe estar en el siguiente formato JSON:

    ```json
    {{
    "periodo": "01-12-2021",
    "trabajadores": [
        {{
        "worker_id": "GAFOJ",
        "base_contingencias_comunes": 3170.19,
        "dias_cotizados": 30,
        "periodo": "01-12-2021"
        }},
        {{
        "worker_id": "LAMAA",
        "base_contingencias_comunes": 2860.52,
        "dias_cotizados": 28, 
        "periodo": "01-12-2021"
        }}
    ]
    }}
    ```
    ⚠️ Devuelve solo un JSON válido con el formato especificado. No incluyas explicaciones ni texto adicional.

    Contenido del documento:
    {text}
    """
        return self._query_openai(prompt, "rnt")

    def extract_from_idc(self, text: str) -> Dict[str, Any]:
        prompt = f"""
Eres un asistente que analiza documentos IDC.
Busca la sección final del documento donde aparecen los tipos de cotización y extrae el valor del campo \"TOTAL\" (porcentaje total).
Devuelve la salida en formato:
{{ "porcentaje_total_it": 1.5 }}

Contenido del documento:
{text}
"""
        return self._query_openai(prompt)

    def extract_from_convenio(self, text: str) -> Dict[str, Any]:
        prompt = f"""
Eres un asistente que revisa convenios laborales.
Busca el número de horas anuales de trabajo (por ejemplo: \"1.708 h\", \"1.760 horas\", etc.).
Devuelve la salida en formato:
{{ "horas_convenio_anuales": 1708 }}

Contenido del documento:
{text}
"""
        return self._query_openai(prompt)