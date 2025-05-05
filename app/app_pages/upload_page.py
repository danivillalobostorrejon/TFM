import streamlit as st
import pandas as pd
import os
import json


def show(pdf_preprocessor, llm_classifier, db):
    """
    Display the Upload Documents page

    Args:
        pdf_preprocessor (PDFProcessor): PDF processing utility
        llm_classifier (LLMClassifier): LLM classification utility
        db (Database): Database instance
    """
    st.title("Upload Worker Documents")

    uploaded_files = st.file_uploader("Upload PDF documents", type="pdf", accept_multiple_files=True)

    if uploaded_files and st.button("Process Documents"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Save uploaded files temporarily
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)

        saved_files = []
        for i, file in enumerate(uploaded_files):
            file_path = os.path.join(temp_dir, file.name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            saved_files.append(file_path)

            progress = (i + 1) / len(uploaded_files) * 50
            progress_bar.progress(int(progress))
            status_text.text(f"Saving file {i+1}/{len(uploaded_files)}")

        # Procesar PDFs por documento y clasificar tipo una sola vez
        classified_docs = []
        for i, file_path in enumerate(saved_files):
            full_text = pdf_preprocessor.extract_text_from_pdf(file_path)
            page_texts = pdf_preprocessor.extract_text_by_page(file_path)

            try:
                doc_type = llm_classifier.classify_document_type(full_text)
                print(f"Clasificado como: {doc_type}")
            except Exception as e:
                st.warning(f"No se pudo clasificar el archivo {os.path.basename(file_path)}: {e}")
                continue

            for page_num, page_text in enumerate(page_texts):
                try:
                    if doc_type == "modelo_190":
                        structured_data = llm_classifier.extract_from_modelo_190(page_text)
                        structured_data['worker_id'] = pdf_preprocessor.generar_id(structured_data['worker_name'])
                    elif doc_type == "10t":
                        structured_data = llm_classifier.extract_from_10t(page_text)
                    elif doc_type == "idc":
                        structured_data = llm_classifier.extract_from_idc(page_text)
                    elif doc_type == "convenio":
                        structured_data = llm_classifier.extract_from_convenio(page_text)
                    elif doc_type == "rnt":
                        structured_data = llm_classifier.extract_from_rnt(page_text)
                    else:
                        continue  # Documento irrelevante

                    classified_docs.append({
                        'filename': os.path.basename(file_path),
                        'page': page_num + 1,
                        'doc_type': doc_type,
                        'data': structured_data
                    })
                except Exception as e:
                    st.warning(f"Página {page_num+1} de {os.path.basename(file_path)} no se procesó: {e}")

            progress = (i + 1) / len(saved_files) * 50 + 50
            progress_bar.progress(int(progress))
            status_text.text(f"Clasificando páginas del archivo {i+1}/{len(saved_files)}")

        # Insertar en la base de datos si los datos contienen info de trabajador
        for doc in classified_docs:
            info = doc['data']
            if doc['doc_type'] == "modelo_190":
                db.insert_worker({
                    'worker_id': info['worker_id'],
                    'worker_name': info['worker_name'],
                    'percepcion_integra': float(info['percepcion_integra']),
                })
            elif doc['doc_type'] == "rnt":
                for worker in info:
                    db.insert_contingencias_comunes({
                        "worker_id": worker['worker_id'],
                        "base_contingencias_comunes": worker['base_contingencias_comunes'],
                        "dias_cotizados": worker['dias_cotizados'],
                        "periodo": worker['periodo'],
                    })
            elif doc['doc_type'] == "convenio":
                value = info.get('horas_convenio_anuales')

                if value is not None:
                    if float(value) > 0:
                        db.insert_convenio({
                            'horas_convenio_anuales': float(value),
                        })
            if all(k in info for k in ['worker_id', 'worker_name', 'hourly_rate', 'hours_worked', 'work_date']):

                db.insert_work_hours(
                    info['worker_id'],
                    float(info['hours_worked']),
                    info['work_date']
                )

        progress_bar.progress(100)
        status_text.text("Processing complete!")

        # Mostrar resultados
        st.subheader("Páginas Procesadas con Datos")
        result_df = pd.DataFrame([
            {
                'Filename': doc['filename'],
                'Page': doc['page'],
                'Doc Type': doc['doc_type'],
                **doc['data']
            } for doc in classified_docs if isinstance(doc['data'], dict)
        ])
        st.dataframe(result_df)

        # Clean up temporary files
        for file_path in saved_files:
            if os.path.exists(file_path):
                os.remove(file_path)
