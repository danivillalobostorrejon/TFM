import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def show(calculator, db):
    """
    Display the Calculate Costs page
    
    Args:
        calculator (CostCalculator): Cost calculator instance
        db (Database): Database instance
    """
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
