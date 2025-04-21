# main.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import json

from pdf_processor import PDFProcessor
from llm_classifier import LLMClassifier
from database import Database
from calculator import CostCalculator
from chatbot import ChatBot

# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# App configuration
st.set_page_config(page_title="Worker Cost Calculator", layout="wide")

# Sidebar for navigation
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

if page == "Upload Documents":
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
        
        # Process PDFs and extract content
        processed_docs = []
        for i, file_path in enumerate(saved_files):
            text_content = pdf_processor.extract_text_from_pdf(file_path)
            processed_docs.append({
                'filename': os.path.basename(file_path),
                'content': text_content
            })
            
            progress = 50 + (i + 1) / len(saved_files) * 25
            progress_bar.progress(int(progress))
            status_text.text(f"Extracting text from file {i+1}/{len(saved_files)}")
        
        # Classify with LLM
        classified_docs = []
        for i, doc in enumerate(processed_docs):
            try:
                worker_info_str = llm_classifier.classify_worker_info(doc['content'])
                worker_info = json.loads(worker_info_str)
                classified_docs.append({
                    'filename': doc['filename'],
                    'worker_info': worker_info
                })
            except Exception as e:
                st.error(f"Error classifying document {doc['filename']}: {str(e)}")
                
            progress = 75 + (i + 1) / len(processed_docs) * 25
            progress_bar.progress(int(progress))
            status_text.text(f"Classifying document {i+1}/{len(processed_docs)}")
        
        # Insert into database
        for doc in classified_docs:
            info = doc['worker_info']
            db.insert_worker({
                'worker_id': info['worker_id'],
                'worker_name': info['worker_name'],
                'hourly_rate': float(info['hourly_rate'])
            })
            
            db.insert_work_hours(
                info['worker_id'],
                float(info['hours_worked']),
                info['work_date']
            )
        
        progress_bar.progress(100)
        status_text.text("Processing complete!")
        
        # Display results in a table
        st.subheader("Processed Documents")
        result_df = pd.DataFrame([
            {
                'Filename': doc['filename'],
                'Worker': doc['worker_info']['worker_name'],
                'ID': doc['worker_info']['worker_id'],
                'Rate': doc['worker_info']['hourly_rate'],
                'Hours': doc['worker_info']['hours_worked'],
                'Date': doc['worker_info']['work_date']
            } for doc in classified_docs
        ])
        st.dataframe(result_df)
        
        # Clean up temporary files
        for file_path in saved_files:
            if os.path.exists(file_path):
                os.remove(file_path)

elif page == "View Workers":
    st.title("Worker Information")
    
    workers = db.get_all_workers()
    
    if workers:
        df = pd.DataFrame(workers)
        st.dataframe(df)
    else:
        st.info("No workers found in the database. Please upload documents first.")

elif page == "Calculate Costs":
    st.title("Cost Calculator")
    
    workers = db.get_all_workers()
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    if workers:
        # Worker selection
        worker_options = ["All Workers"] + [f"{w['worker_name']} (ID: {w['worker_id']})" for w in workers]
        selected_worker = st.selectbox("Select Worker", worker_options)
        
        if st.button("Calculate Cost"):
            with st.spinner("Calculating..."):
                if selected_worker == "All Workers":
                    result = calculator.calculate_all_workers_cost(start_date_str, end_date_str)
                    
                    # Display summary
                    st.subheader("Summary")
                    col1, col2 = st.columns(2)
                    col1.metric("Total Hours", f"{result['total_hours']:.2f}")
                    col2.metric("Total Cost", f"${result['total_cost']:.2f}")
                    
                    # Display detailed breakdown
                    st.subheader("Breakdown by Worker")
                    worker_results = result['workers']
                    if worker_results:
                        result_df = pd.DataFrame([
                            {
                                'Worker': w['worker_name'],
                                'ID': w['worker_id'],
                                'Rate': f"${w['hourly_rate']:.2f}",
                                'Hours': f"{w['total_hours']:.2f}",
                                'Cost': f"${w['total_cost']:.2f}"
                            } for w in worker_results
                        ])
                        st.dataframe(result_df)
                    else:
                        st.info("No work hours recorded in this date range.")
                else:
                    # Extract worker_id from selection
                    worker_id = selected_worker.split("ID: ")[1][:-1]
                    result = calculator.calculate_worker_cost(worker_id, start_date_str, end_date_str)
                    
                    if result:
                        st.subheader(f"Cost for {result['worker_name']}")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Hourly Rate", f"${result['hourly_rate']:.2f}")
                        col2.metric("Total Hours", f"{result['total_hours']:.2f}")
                        col3.metric("Total Cost", f"${result['total_cost']:.2f}")
                    else:
                        st.info("No work hours recorded for this worker in the selected date range.")
    else:
        st.info("No workers found in the database. Please upload documents first.")

elif page == "Chat":
    st.title("Chat with Worker Cost Assistant")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about worker costs..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get context data for the chatbot
        with st.spinner("Thinking..."):
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            # Get all worker cost data to provide context to the chatbot
            context = calculator.calculate_all_workers_cost(start_date, end_date)
            
            # Get response from chatbot
            response = chatbot.get_response(prompt, context)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Display assistant response
            with st.chat_message("assistant"):
                st.write(response)
