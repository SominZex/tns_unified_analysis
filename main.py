import streamlit as st
import subprocess
import os

st.set_page_config(page_title="The New Shop:Data Factory", layout="wide")

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

st.markdown("<h1 style='text-align: center;'>TNS Unified Analysis Dashboard</h1>", unsafe_allow_html=True)


analysis_type = st.selectbox(
    "Choose an analysis type", 
    ["Select", "Product Analysis", "Category Analysis", "Store Analysis", "Brand Analysis"]
)

if analysis_type == "Product Analysis":
    st.subheader("Running Product Analysis (Switch the browser tab)")
    subprocess.run(["streamlit", "run", os.path.join("product_analysis", "main.py")])

elif analysis_type == "Category Analysis":
    st.subheader("Running Category Analysis (Switch the browser tab)")
    subprocess.run(["streamlit", "run", os.path.join("category_analysis", "main.py")])

elif analysis_type == "Store Analysis":
    st.subheader("Running Store Analysis (Switch the browser tab)")
    subprocess.run(["streamlit", "run", os.path.join("store_analysis", "main.py")])

elif analysis_type == "Brand Analysis":
    st.subheader("Running Brand Analysis (Switch the browser tab)")
    subprocess.run(["streamlit", "run", os.path.join("brand_analysis", "main.py")])

else:
    st.warning("Select an analysis type to proceed.")
