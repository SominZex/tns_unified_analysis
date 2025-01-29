import streamlit as st
import pandas as pd
from utils.data_loader import load_data_from_directory
from store_analysis.analysis.weekly_sales import weekly_sales_analysis
from store_analysis.analysis.store_performance_analysis import store_performance_analysis
from store_analysis.analysis.hourly_sales import hourly_sales_analysis
from store_analysis.analysis.category_breakdown import category_breakdown_analysis
from store_analysis.analysis.profit_margin_analysis import profit_margin_analysis
from store_analysis.analysis.top_products import top_products_analysis
from store_analysis.analysis.brand_performance_analysis import brand_performance_analysis
from store_analysis.analysis.daily_sales_analysis import daily_sales_analysis


# Cache data loading to optimize performance
@st.cache_data
def load_optimized_data_from_directory():
    data = load_data_from_directory()
    data['orderDate'] = pd.to_datetime(data['orderDate'], utc=True)
    return data

@st.cache_data
def date_filtered_data(_data, start_date, end_date):
    mask = (_data['orderDate'] >= start_date) & (_data['orderDate'] <= end_date)
    return _data[mask]

# Cache data filtering to optimize performance
@st.cache_data
def filter_data(_data, stores, start_date, end_date):
    mask = (
        (_data['orderDate'] >= start_date) &
        (_data['orderDate'] <= end_date) &
        (_data['storeName'].isin(stores))
    )
    return _data[mask]

# Load data into session state
if 'data' not in st.session_state:
    with st.spinner('Loading data...'):
        st.session_state.data = load_optimized_data_from_directory()

data = st.session_state.data

if data is not None:
    # Sidebar filters
    with st.sidebar:
        min_date, max_date = data['orderDate'].min(), data['orderDate'].max()

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", min_date)
        with col2:
            end_date = st.date_input("End Date", max_date)

        # Convert date inputs to UTC
        start_date = pd.to_datetime(start_date, utc=True)
        end_date = pd.to_datetime(end_date, utc=True)

        # Top stores selection
        unique_stores = data['storeName'].unique()
        n_stores_available = len(unique_stores)
        n_stores = st.number_input(
            "Select number of top stores to analyze",
            min_value=1,
            max_value=n_stores_available,
            value=min(50, n_stores_available),
        )
        top_stores = data['storeName'].value_counts().head(n_stores).index.tolist()
        selected_stores_sidebar = st.multiselect("Select stores for analysis", options=top_stores)

    # Default to selected or all top stores
    selected_stores = selected_stores_sidebar if selected_stores_sidebar else top_stores


    # Filter data
    filtered_data = filter_data(data, selected_stores, start_date, end_date)

    # Perform analysis
    if filtered_data is not None and not filtered_data.empty:
        try:
            with st.spinner('Analyzing data...'):

                # Filter the entire data by the selected date range (no store filter)
                date_filtered = date_filtered_data(data, start_date, end_date)

                store_performance_analysis(data, date_filtered, selected_stores)
                weekly_sales_analysis(filtered_data, selected_stores_sidebar)
                daily_sales_analysis(filtered_data, selected_stores, selected_stores_sidebar)
                hourly_sales_analysis(filtered_data, selected_stores, selected_stores_sidebar)

                if selected_stores_sidebar:
                    brand_performance_analysis(filtered_data, date_filtered, selected_stores)
                    category_breakdown_analysis(filtered_data, selected_stores)
                    top_products_analysis(filtered_data)

                profit_margin_analysis(filtered_data)
        except Exception as e:
            st.error(f"An error occurred during analysis: {str(e)}")
            st.exception(e)
    else:
        st.warning("No data found for the selected criteria.")
else:
    st.warning("No data available. Please ensure the data directory is correctly configured.")
