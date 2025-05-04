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
        
        # Process PDFs and extract content
        processed_docs = []
        for i, file_path in enumerate(saved_files):
            text_content = pdf_preprocessor.extract_text_from_pdf(file_path)
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
