import streamlit as st

def show(chatbot, pdf_preprocessor, llm_classifier, db, session_state):
    st.title("Chat con el sistema")

    # Mostrar historial del chat
    for message in session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ========= A. Subida de documentos laborales (procesados en la BBDD) =========
    st.markdown("### 📎 Subida de documentos laborales (Modelo 190, RNT, 10T...)")
    uploaded_files = st.file_uploader("Puedes subir documentos PDF laborales", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        resultados = chatbot.process_uploaded_files(uploaded_files, pdf_preprocessor, llm_classifier, db)
        if not resultados:
            st.warning("No se encontraron resultados en los documentos subidos.")
        respuesta = "\n".join(set(resultados))

        for file in uploaded_files:
            session_state.messages.append({"role": "user", "content": f"[📎 Documento subido: {file.name}]"})
            with st.chat_message("user"):
                st.markdown(f"[📎 Documento subido: {file.name}]")

        session_state.messages.append({"role": "assistant", "content": respuesta})
        with st.chat_message("assistant"):
            st.text_area("Resultados del procesamiento", value=respuesta, height=300, disabled=True)

    # ========= B. Documento de planificación como contexto =========
    st.markdown("### 📝 Documento de planificación (solo como contexto para el chat)")
    project_file = st.file_uploader("Opcional: sube un documento de planificación (memoria técnica, etc.)", type="pdf", key="planificacion")

    pdf_context_text = ""
    if project_file:
        pdf_context_text = pdf_preprocessor.extract_text_from_pdf(project_file)
        st.success(f"Documento '{project_file.name}' cargado para contextualizar futuras consultas.")

    # ========= Entrada del usuario =========
    prompt = st.chat_input("Escribe tu consulta aquí...")
    if prompt:
        session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Preparar contexto combinado
        context = db.get_all_workers()
        if pdf_context_text:
            context = {
                "worker_data": context,
                "documento_proyecto": pdf_context_text  # Limitar longitud si es necesario
            }

        response = chatbot.get_response(prompt, context=context)
        session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
