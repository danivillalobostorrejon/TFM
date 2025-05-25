# chatbot.py
from typing import Dict, Any, List
import openai
import json
import decimal
import os
import json
import tempfile
import streamlit as st

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

        context_json = json.dumps(context, default=decimal_default, indent=2)

        system_message = f"""
Eres un asistente inteligente para una aplicación de asignación eficiente de tareas y cálculo de costes laborales.

Has recibido un documento PDF que contiene la planificación de un proyecto, incluyendo:
- Fases del proyecto
- Duración estimada de cada fase
- Tareas previstas en cada fase
- Participación del personal técnico, con horas asignadas por año

También tienes acceso al coste por hora de cada trabajador, previamente calculado y almacenado en la base de datos.

Tu objetivo es:

1. Leer y entender la estructura del proyecto (fases y tareas).
2. Leer las horas asignadas por trabajador y año.
3. Realizar una asignación eficiente de tareas, teniendo en cuenta:
   - Las horas disponibles por trabajador.
   - Su coste por hora.
   - La duración estimada de cada fase.
4. Calcular el coste total estimado por trabajador y por fase del proyecto.
5. Devolver una tabla resumen con la asignación y coste total por trabajador.

Formato de salida esperado (en JSON o tabla):

```json
{{
  "asignacion": [
    {{
      "fase": "Fase 1 - Análisis técnico",
      "trabajador": "Jose Garcia Fontecha",
      "horas_asignadas": 120,
      "coste_por_hora": 17.93,
      "coste_total": 2151.60
    }},
    {{
      "fase": "Fase 2 - Diseño",
      "trabajador": "Andrea Sáez Benito",
      "horas_asignadas": 100,
      "coste_por_hora": 22.50,
      "coste_total": 2250.00
    }}
  ]
}}
````

Ten en cuenta:

* Si no dispones del coste por hora de un trabajador, indícalo.
Si falta información, indica qué datos faltan:
- salario bruto (llamado "percepción íntegra"), indica que faltan los datos del modelo 190 o 10T
- Un número de horas trabajadas registrado. Indica que faltan los datos del convenio colectivo.
- Datos de RNT (base de contingencias comunes y días cotizados), indica que faltan los datos del RNT
* Si las horas asignadas superan la disponibilidad estimada anual, emite una advertencia.

Contenido del documento a analizar:
{context_json}
    """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content

    def process_uploaded_files(self, uploaded_files, pdf_preprocessor, llm_classifier, db):

        processed = []

        with tempfile.TemporaryDirectory() as temp_dir:
            saved_files = []
            for file in uploaded_files:
                path = os.path.join(temp_dir, file.name)
                with open(path, "wb") as f:
                    f.write(file.getbuffer())
                saved_files.append(path)

            for file_path in saved_files:
                full_text = pdf_preprocessor.extract_text_from_pdf(file_path)
                pages = pdf_preprocessor.extract_text_by_page(file_path)
                try:
                    doc_type = llm_classifier.classify_document_type(full_text)
                except Exception as e:
                    processed.append(f"No se pudo clasificar el archivo {os.path.basename(file_path)}: {e}")
                for page_num, page_text in enumerate(pages):
                    try:
                        structured_data = llm_classifier.extract_structured_data(text=page_text, doc_type=doc_type)
                        if doc_type != "rnt":
                            worker_id = pdf_preprocessor.generar_id(structured_data.get("worker_name", ""))
                        # Insertar según el tipo
                        if doc_type in ("modelo_190", "10t"):
                            db.insert_worker({
                                "worker_id": worker_id,
                                "worker_name": structured_data["worker_name"],
                                "percepcion_integra": structured_data["percepcion_integra"],
                                "year": structured_data['year'],
                                "company_id": structured_data['company_id'],
                                "company_name": structured_data['company_name'],
                            })

                        elif doc_type == "rnt":
                            for entry in structured_data:
                                db.insert_contingencias_comunes({
                                    "worker_id": entry["worker_id"],
                                    "base_contingencias_comunes": entry["base_contingencias_comunes"],
                                    "dias_cotizados": entry["dias_cotizados"],
                                    "periodo": entry["periodo"],
                                    "year": entry['year'],
                                    "company_id": entry["company_id"],
                                    "company_name": entry["company_name"],
                                })
                        elif doc_type == "convenio":
                            convenio_inserted = False
                            if convenio_inserted:
                                continue
                            if "year" in structured_data:
                                # Use the year from structured_data if available
                                aux_year = structured_data["year"]

                            # Check if structured_data contains both "horas_convenio_anuales" and "year"
                            if structured_data.get("horas_convenio_anuales") is not None and structured_data.get("year") is not None:
                                db.insert_convenio({
                                    "horas_convenio_anuales": structured_data["horas_convenio_anuales"],
                                    "year": structured_data['year']
                                })
                                convenio_inserted = True
                            
                            if structured_data.get("horas_convenio_anuales") is not None and structured_data.get("year") is None:
                                if aux_year is None:
                                    continue
                                db.insert_convenio({
                                    "horas_convenio_anuales": structured_data["horas_convenio_anuales"],
                                    "year": aux_year
                                })

                        processed.append(f"{os.path.basename(file_path)} página {page_num+1}")
                    except Exception as e:
                        # st.warning(f"Error en {os.path.basename(file_path)} página {page_num+1}: {e} - {structured_data}")
                        continue

        return processed

