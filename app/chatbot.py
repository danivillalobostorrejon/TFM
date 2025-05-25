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

Si falta información, indica qué datos faltan:
- salario bruto (llamado "percepción íntegra"), indica que faltan los datos del modelo 190 o 10T
- Un número de horas trabajadas registrado. Indica que faltan los datos del convenio colectivo.
- Datos de RNT (base de contingencias comunes y días cotizados), indica que faltan los datos del RNT

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

