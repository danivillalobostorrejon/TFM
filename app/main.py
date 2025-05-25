# main.py (modificado)
import streamlit as st
import os

from pdf_preprocessor import PDFProcessor
from llm_classifier import LLMClassifier
from database import Database
from chatbot import ChatBot

# Importación directa de los módulos de las páginas
from app_pages.view_workers_page import show as show_view_workers_page
from app_pages.chat_page import show as show_chat_page

# App configuration
st.set_page_config(page_title="Worker Cost Calculator", layout="wide")

# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# # Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page", 
    [
        #"Upload Documents", 
        "Chat",
        "View Workers", 
    ])

# Initialize components
db = Database()
pdf_processor = PDFProcessor()
llm_classifier = LLMClassifier(api_key=os.getenv('OPENAI_API_KEY'))
chatbot = ChatBot(api_key=os.getenv('OPENAI_API_KEY'))

# Create database tables if they don't exist
if os.getenv('CLEAN_DB') == 'true':
    db.clean_database()
db.create_tables()

# Route to the correct page
# if page == "Upload Documents":
#     show_upload_page(pdf_processor, llm_classifier, db)
if page == "View Workers":
    show_view_workers_page(db)
elif page == "Chat":
    show_chat_page(chatbot, pdf_processor, llm_classifier, db, st.session_state)

