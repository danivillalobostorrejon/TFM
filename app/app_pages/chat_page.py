import streamlit as st
from datetime import datetime, timedelta

def show(chatbot, database, session_state):
    """
    Display the Chat page
    
    Args:
        chatbot (ChatBot): Chatbot instance
        calculator (CostCalculator): Cost calculator instance
        session_state (dict): Streamlit session state
    """
    st.title("Chat with Worker Cost Assistant")
    
    # Display chat messages
    for message in session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about worker costs..."):
        # Add user message to chat history
        session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get context data for the chatbot
        with st.spinner("Thinking..."):
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            # Get all worker cost data to provide context to the chatbot
            context = database.get_all_workers()
            
            # Get response from chatbot
            response = chatbot.get_response(prompt, context)
            
            # Add assistant response to chat history
            session_state.messages.append({"role": "assistant", "content": response})
            
            # Display assistant response
            with st.chat_message("assistant"):
                st.write(response)
