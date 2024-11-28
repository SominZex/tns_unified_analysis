import streamlit as st
import subprocess
import os

# Set the page layout to wide
st.set_page_config(page_title="Unified Analysis Dashboard", layout="wide")

# Apply custom CSS to increase content width
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


# Use a dropdown menu (selectbox) instead of buttons
analysis_type = st.selectbox(
    "Choose an analysis type", 
    ["Select", "Product Analysis", "Category Analysis", "Store Analysis", "Brand Analysis"]
)

# Run corresponding analysis based on the selected option
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
    st.warning("Please select an analysis type to proceed.")
