import streamlit as st
import pandas as pd

def show(db):
    """
    Display the View Workers page
    
    Args:
        db (Database): Database instance
    """
    st.title("Worker Information")
    
    workers = db.get_all_workers()
    
    if workers:
        df = pd.DataFrame(workers)
        st.dataframe(df)
    else:
        st.info("No workers found in the database. Please upload documents first.")
