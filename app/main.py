# main.py (modificado)
import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import json

from pdf_preprocessor import PDFProcessor
from llm_classifier import LLMClassifier
from database import Database
from calculator import CostCalculator
from chatbot import ChatBot

# Importación directa de los módulos de las páginas
from app_pages.upload_page import show as show_upload_page
from app_pages.view_workers_page import show as show_view_workers_page
from app_pages.calculate_costs_page import show as show_calculate_costs_page
from app_pages.chat_page import show as show_chat_page

# App configuration
st.set_page_config(page_title="Worker Cost Calculator", layout="wide")

# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# # Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a page", ["Upload Documents", "View Workers", "Calculate Costs", "Chat"])

# Initialize components
db = Database()
pdf_processor = PDFProcessor()
llm_classifier = LLMClassifier(api_key=os.getenv('OPENAI_API_KEY'))
calculator = CostCalculator(db)
chatbot = ChatBot(api_key=os.getenv('OPENAI_API_KEY'))

# Create database tables if they don't exist
db.create_tables()

# Route to the correct page
if page == "Upload Documents":
    show_upload_page(pdf_processor, llm_classifier, db)
elif page == "View Workers":
    show_view_workers_page(db)
elif page == "Calculate Costs":
    show_calculate_costs_page(calculator, db)
elif page == "Chat":
    show_chat_page(chatbot, db, st.session_state)
