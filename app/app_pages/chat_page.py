
import streamlit as st

def show(chatbot, pdf_preprocessor, llm_classifier, db, session_state):
    st.title("Chat con el sistema")

    # Mostrar historial
    for message in session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Subida de documentos dentro del chat
    uploaded_files = st.file_uploader("Puedes subir documentos PDF para procesarlos", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        resultados = chatbot.process_uploaded_files(uploaded_files, pdf_preprocessor, llm_classifier, db)
        if not resultados:
            st.warning("No se encontraron resultados en los documentos subidos.")
        respuesta = set(resultados)
        respuesta = "\n".join(resultados)

        for file in uploaded_files:
            session_state.messages.append({"role": "user", "content": f"[📎 Documento subido: {file.name}]"})
            with st.chat_message("user"):
                st.markdown(f"[📎 Documento subido: {file.name}]")

        session_state.messages.append({"role": "assistant", "content": respuesta})
        with st.chat_message("assistant"):
            # Scrollable text area para mostrar la respuesta
            st.text_area("Resultados del procesamiento", value=respuesta, height=300, disabled=True)


    # Entrada del usuario
    prompt = st.chat_input("Escribe tu consulta aquí...")
    if prompt:
        session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        response = chatbot.get_response(prompt, context=db.get_all_workers())
        session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)