import streamlit as st
import os
import runpy

st.set_page_config(page_title="TNS Unified Analysis Dashboard", layout="wide")

st.markdown(
    """
    <style>
    .main .block-container {
        max-width: 90% !important;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

st.markdown("<h1 style='text-align: center;'>Unified Analysis Dashboard</h1>", unsafe_allow_html=True)

analysis_type = st.selectbox(
    "Choose an analysis type", 
    ["Product Analysis", "Category Analysis", "Store Analysis", "Brand Analysis"]
)

def run_analysis(script_name):
    st.subheader(f"Running {script_name}")
    try:
        script_path = os.path.join(script_name, "main.py")
        runpy.run_path(script_path)
    except Exception as e:
        st.error(f"An error occurred while running {script_name} analysis: {e}")

if analysis_type == "Product Analysis":
    run_analysis("product_analysis")

elif analysis_type == "Category Analysis":
    run_analysis("category_analysis")

elif analysis_type == "Store Analysis":
    run_analysis("store_analysis")

elif analysis_type == "Brand Analysis":
    run_analysis("brand_analysis")

else:
    st.warning("Please select an analysis type to proceed.")
