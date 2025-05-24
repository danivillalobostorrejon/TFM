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

    def extract_structured_data(self, text: str, doc_type: str) -> Dict[str, Any]:

        if doc_type == "modelo_190":
            return self.extract_from_modelo_190(text)
        elif doc_type == "10t":
            return self.extract_from_10t(text)
        elif doc_type == "rnt":
            return self.extract_from_rnt(text)
        elif doc_type == "idc":
            return self.extract_from_idc(text)
        elif doc_type == "convenio":
            return self.extract_from_convenio(text)
        else:
            raise ValueError("No se pudo clasificar el tipo de documento.")

    def _query_openai(self, prompt: str, doc_type: str = None) -> Dict[str, Any]:
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un asistente experto en analizar documentos laborales y fiscales."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content.strip()
        # print(content)

        if doc_type in ("modelo_190", "convenio", "10t"):
            match = re.search(r"\{.*\}", content, re.DOTALL)
        elif doc_type == "rnt":
            match = re.search(r"\[\s*\{.*?\}\s*(,\s*\{.*?\}\s*)*\]", content, re.DOTALL)

        if not match:
            raise ValueError(f"No se encontró ningún JSON válido en la respuesta del modelo.")

        json_text = match.group()

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al parsear JSON: {e}\nContenido:\n{json_text}")

    def extract_from_modelo_190(self, text: str) -> Dict[str, Any]:
        prompt = f"""
Eres un asistente experto en análisis de documentos fiscales en formato PDF.

Tu tarea consiste en extraer información estructurada de un documento, concretamente los siguientes campos:

1. `"worker_name"`: el nombre completo del trabajador tal como aparece en el documento.
2. `"percepcion_integra"`: el valor numérico asociado al campo "Percepción íntegra". Este valor representa el salario bruto anual. 
   ⚠️ Si el número está en formato europeo (por ejemplo: `24.214,44` o `24 214,44` o `24,214.44`), debes normalizarlo al formato decimal estadounidense: `24214.44` (punto como separador decimal y sin separadores de miles).
3. `"year"`: el año fiscal indicado en el documento. Aparece en el campo "Ejercicio", normalmente cerca del encabezado o inicio de la página.
4. `"worker_id"`: un identificador generado tomando las dos primeras letras del primer apellido, las dos primeras letras del segundo apellido, y la inicial del nombre. Por ejemplo, si el nombre es "Jose Garcia Fontecha", el identificador es `"GAFOJ"`.
5. `"company_name"`: el nombre de la empresa que aparece en el documento. Que aparece como "Apellidos y nombre o razón social". Si no aparece, puedes dejarlo como "no definido".
6. `"company_id"`: el CIF de la empresa que aparece en el documento. Que aparece como "NIF del declarante" (Ejemplo: "NIF: B24532178"), si no aparece, puedes dejarlo como "no definido".

Devuelve exclusivamente un objeto JSON válido con esta información.

Ejemplo de salida esperada:
{{
    "worker_name": "Jose Garcia Fontecha",
    "percepcion_integra": 24214.44,
    "year": 2021,
    "worker_id": "GAFOJ",
    "company_name": "Nombre de la empresa",
    "company_id": "B24532178"
}}

Contenido del documento:
{text}

"""
        return self._query_openai(prompt, "modelo_190")

    def extract_from_10t(self, text: str) -> Dict[str, Any]:
        prompt = f"""
Eres un asistente experto en el análisis de documentos fiscales en formato PDF.

Tu tarea consiste en extraer la siguiente información de un documento fiscal (Documento 10T):

1. `"worker_name"`: el nombre completo del trabajador tal y como aparece en el documento.
2. `"percepcion_integra"`: el valor numérico asociado al campo "Rendimiento a integrar", que representa el salario bruto anual.
    ⚠️ Si el número está en formato europeo (por ejemplo: `24.214,44` o `24 214,44` o `24,214.44`), debes normalizarlo al formato decimal estadounidense: `24214.44` (punto como separador decimal y sin separadores de miles).
3. `"year"`: el año fiscal correspondiente, que aparece en el campo "Ejercicio" al principio del documento o página.
4. `"worker_id"`: un identificador generado tomando las dos primeras letras del primer apellido, las dos primeras letras del segundo apellido, y la primera letra del nombre. Por ejemplo, para "Jose Garcia Fontecha", el `worker_id` sería `"GAFOJ"`.
5. "company_name": el nombre de la empresa que aparece en el documento. Que aparece como "Apellidos y nombre o razón social"
6. "company_id": el CIF de la empresa que aparece en el documento. Que aparece como "NIF" (Ejemplo: "NIF: B24532178")

Devuelve únicamente un objeto JSON válido con esta información.

Ejemplo de salida esperada:
{{
    "worker_name": "Jose Garcia Fontecha",
    "percepcion_integra": 60000.00,
    "worker_id": "GAFOJ",
    "year": 2021
    "company_name": "Nombre de la empresa",
    "company_id": "B24532178"
}}

Contenido del documento:
{text}
"""
        return self._query_openai(prompt, "10t")

    def extract_from_rnt(self, text: str) -> str:
        prompt = f"""
    Eres un asistente que extrae información de documentos RNT mensuales de la Seguridad Social.

    Tu tarea es:

    1. Leer el texto y devolver una lista de trabajadores, donde cada uno tiene:
        - `"worker_id"`: el identificador del trabajador (CAF), de 5 letras mayúsculas.
        - `"base_contingencias_comunes"`: número decimal, por ejemplo: 3170.19
        - `"dias_cotizados"`: número entero, por ejemplo: 30
        - "year": año de la liquidación, por ejemplo: 2021, sale del campo "Periodo de liquidación" (ver más abajo).
        - "company_id": el CIF de la empresa que aparece en el documento. Que aparece como "Código de empresario" (Ejemplo: "Código de empresario: B24532178")
        - "company_name": el nombre de la empresa que aparece en el documento. Que aparece como "Razón social" (Ej. Razón social: TALLERES PACO, SL)

    2. Extraer también el **periodo de liquidación** del documento. Aparece como:
    `"Periodo de liquidación 12/2021-12/2021"`
    Interprétalo y devuelve el valor `"01-12-2021"` (día 1 del mes indicado).

    3. El campo "dias_cotizados" debe ser un número entero sin ceros iniciales.

    El resultado debe estar en el siguiente formato JSON:

    ```json
    {{
    "trabajadores": [
        {{
        "worker_id": "GAFOJ",
        "base_contingencias_comunes": 3170.19,
        "dias_cotizados": 30,
        "periodo": "01-12-2021"
        "year": 2021,
        "company_id": "B24532178",
        "company_name": "TALLERES PACO, SL"
        }},
        {{
        "worker_id": "LAMAA",
        "base_contingencias_comunes": 2860.52,
        "dias_cotizados": 28, 
        "periodo": "01-12-2021"
        "year": 2021,
        "company_id": "B24532178",
        "company_name": "TALLERES PACO, SL"
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
Eres un asistente experto en la revisión de convenios laborales.

Tu tarea consiste en extraer dos datos clave del documento:

1. `"horas_convenio_anuales"`: el número de horas anuales de trabajo que establece el convenio. Puede aparecer en distintos formatos como: `1.708 h`, `1.760 horas`, `1700h`, etc.

2. `"year"`: el año final de la vigencia del convenio. Este aparece típicamente en frases como:
   - “vigencia desde el 1 de enero de 2019 hasta el 31 de diciembre de 2021”
   - “el convenio estará vigente hasta el 31/12/2022”

En estos casos, extrae el año final (por ejemplo, `2021` o `2022`) y úsalo como valor del campo `"year"`.

Devuelve exclusivamente un objeto JSON válido con el siguiente formato:

```json
{{
  "horas_convenio_anuales": 1708,
  "year": 2021
}}
```


Contenido del documento:
{text}
"""
        return self._query_openai(prompt, "convenio")