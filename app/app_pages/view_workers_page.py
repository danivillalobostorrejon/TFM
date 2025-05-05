import streamlit as st
import pandas as pd

def show(db):
    """
    Display the View Workers page
    
    Args:
        db (Database): Database instance
    """
    st.title("Worker Information")
    
    workers = db.get_workers_data()
    
    if workers:
        
        df = pd.DataFrame(workers)
        st.dataframe(df)

        # contingencias_comunes = workers.get("contingencias_comunes", [])
        # st.dataframe(contingencias_comunes)
    else:
        st.info("No workers found in the database. Please upload documents first.")
