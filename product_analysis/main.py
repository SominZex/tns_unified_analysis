import streamlit as st
import pandas as pd
import plotly.express as px
import gc
from utils.data_loader import load_data_from_directory
from product_analysis.analysis.weekly_sales import weekly_sales_analysis 
from product_analysis.analysis.store_performance_analysis import store_performance_analysis
from product_analysis.analysis.hourly_sales import hourly_sales_analysis
from product_analysis.analysis.category_breakdown import category_breakdown_analysis
from product_analysis.analysis.profit_margin_analysis import profit_margin_analysis
from product_analysis.analysis.top_products import top_products_analysis
from product_analysis.analysis.category_comparison import category_comparison_analysis
from product_analysis.analysis.product_performance_analysis import product_performance_analysis
from product_analysis.analysis.daily_sales_analysis import daily_sales_analysis
from product_analysis.analysis.affinity_analysis import affinity_analysis

# Page configuration
# st.set_page_config(page_title="Product Analysis Dashboard", layout="wide")

@st.cache_data
def load_optimized_data_from_directory():
    return load_data_from_directory() 

def filter_data(_data, products, stores, start_date, end_date):
    if start_date is not None:
        start_date = pd.to_datetime(start_date, utc=True)
    if end_date is not None:
        end_date = pd.to_datetime(end_date, utc=True)

    _data['orderDate'] = pd.to_datetime(_data['orderDate'], utc=True)

    mask = (_data['orderDate'] >= start_date) & (_data['orderDate'] <= end_date) & \
           (_data['productName'].isin(products)) & (_data['storeName'].isin(stores))
    filtered_data = _data[mask]

    return filtered_data

def filter_store_data(_data, stores, start_date, end_date):
    if start_date is not None:
        start_date = pd.to_datetime(start_date, utc=True)
    if end_date is not None:
        end_date = pd.to_datetime(end_date, utc=True)

    _data['orderDate'] = pd.to_datetime(_data['orderDate'], utc=True)

    # Filter by stores and date range, without filtering by products
    mask = (_data['orderDate'] >= start_date) & (_data['orderDate'] <= end_date) & \
           (_data['storeName'].isin(stores))
    store_filtered_data = _data[mask]
    return store_filtered_data

def get_top_products(data, n=10):
    return data['productName'].value_counts().head(n).index.tolist()

def get_top_stores(data, n=10):
    return data['storeName'].value_counts().head(n).index.tolist()

if 'data' not in st.session_state:
    st.session_state.data = None

with st.sidebar:
    if st.session_state.data is None:
        st.session_state.data = load_optimized_data_from_directory()

    data = st.session_state.data

    if data is not None:
        min_date = data['orderDate'].min()
        max_date = data['orderDate'].max() 

        #FIRST5

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", min_date)
        with col2:
            end_date = st.date_input("End Date", max_date)

        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        unique_products = data['productName'].unique()
        n_products_available = len(unique_products)

        n_products = st.number_input(
            "Select number of top products to analyze",
            min_value=1, 
            max_value=n_products_available, 
            value=min(100, n_products_available),
        )

        top_products = get_top_products(data, n=n_products)

        selected_product_sidebar = st.multiselect(
            "Select products for analysis",
            options=top_products
        )

        unique_stores = data['storeName'].unique()
        n_stores_available = len(unique_stores)

        top_stores = get_top_stores(data, n=n_stores_available)

        selected_stores_sidebar = st.multiselect(
            "Select stores for analysis",
            options=top_stores
        )
    else:
        st.warning("No data found in the 'data' directory.")

def clear_memory():
    gc.collect()

if data is not None:
    required_columns = ['productName', 'storeName', 'orderDate', 'sellingPrice', 'costPrice', 'quantity']
    missing_columns = [col for col in required_columns if col not in data.columns]

    if missing_columns:
        st.error(f"The following required columns are missing from the dataset: {', '.join(missing_columns)}")
        st.stop()

    if data['productName'].isnull().all():
        st.error("'productName' column contains no data. Please upload a valid file.")
        st.stop()

    selected_products = selected_product_sidebar if selected_product_sidebar else top_products
    selected_stores = selected_stores_sidebar if selected_stores_sidebar else top_stores

    filtered_data = filter_data(data, selected_products, selected_stores, start_date, end_date)
    store_filtered_data = filter_store_data(data, selected_stores, start_date, end_date)

    try:
        with st.spinner('Analyzing data...'):
            affinity_data = filter_store_data(data, selected_stores, start_date, end_date)
        
            if len(filtered_data) > 0:
                weekly_sales_analysis(filtered_data, selected_product_sidebar, top_products)
                hourly_sales_analysis(filtered_data, selected_products, selected_stores, selected_product_sidebar)
                profit_margin_analysis(filtered_data, selected_products, selected_product_sidebar)
                st.markdown("<h1 style='text-align: center; color: green;'>Buying Pattern Analysis</h1>", unsafe_allow_html=True)
                affinity_analysis(store_filtered_data, selected_product_sidebar, top_n=20)

                if selected_product_sidebar:
                    product_performance_analysis(filtered_data, selected_products, selected_stores)
                    daily_sales_analysis(filtered_data, selected_products, selected_stores)
                    store_performance_analysis(data, filtered_data, selected_products, selected_stores, start_date, end_date)
                    # category_breakdown_analysis(filtered_data, selected_products)

                clear_memory()
            else:
                st.warning("No data found for the selected criteria.")
    except Exception as e:
        st.error(f"An error occurred during analysis: {str(e)}")
        st.exception(e)
else:
    st.warning("No data found in the 'data' directory.")
