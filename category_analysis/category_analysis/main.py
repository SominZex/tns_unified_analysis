import streamlit as st
import pandas as pd
from utils.data_loader import load_data_from_directory
from category_analysis.analysis.weekly_sales import weekly_sales_analysis
from category_analysis.analysis.store_performance_analysis import store_performance_analysis
from category_analysis.analysis.hourly_sales import hourly_sales_analysis
from category_analysis.analysis.category_breakdown import category_breakdown_analysis
from category_analysis.analysis.profit_margin_analysis import profit_margin_analysis
from category_analysis.analysis.top_products import top_products_analysis
from category_analysis.analysis.category_comparison import category_comparison_analysis
from category_analysis.analysis.category_performance_analysis import category_performance_analysis
from category_analysis.analysis.daily_sales_analysis import daily_sales_analysis


@st.cache_data
def load_optimized_data_from_directory():
    data = load_data_from_directory()
    data['orderDate'] = pd.to_datetime(data['orderDate'], utc=True) 
    return data

@st.cache_data
def filter_data(_data, categories, stores, start_date, end_date):
    mask = (
        (_data['orderDate'] >= start_date) &
        (_data['orderDate'] <= end_date) &
        (_data['categoryName'].isin(categories)) &
        (_data['storeName'].isin(stores))
    )
    return _data[mask]

if 'data' not in st.session_state:
    with st.spinner('Loading data...'):
        st.session_state.data = load_optimized_data_from_directory()

data = st.session_state.data

if data is not None:
    with st.sidebar:
        min_date, max_date = data['orderDate'].min(), data['orderDate'].max()

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", min_date)
        with col2:
            end_date = st.date_input("End Date", max_date)

        start_date = pd.to_datetime(start_date, utc=True)
        end_date = pd.to_datetime(end_date, utc=True)

        unique_categories = data['categoryName'].unique()
        n_categories_available = len(unique_categories)
        n_categories = st.number_input(
            "Select number of top categories to analyze",
            min_value=1,
            max_value=n_categories_available,
            value=min(250, n_categories_available),
        )
        top_categories = data['categoryName'].value_counts().head(n_categories).index.tolist()
        selected_categories_sidebar = st.multiselect("Select categories for analysis", options=top_categories)

        unique_stores = data['storeName'].unique()
        top_stores = data['storeName'].value_counts().head(len(unique_stores)).index.tolist()
        selected_stores_sidebar = st.multiselect("Select stores for analysis", options=top_stores)

    selected_categories = selected_categories_sidebar if selected_categories_sidebar else top_categories
    selected_stores = selected_stores_sidebar if selected_stores_sidebar else top_stores

    filtered_data = filter_data(data, selected_categories, selected_stores, start_date, end_date)

    if filtered_data is not None and not filtered_data.empty:
        try:
            with st.spinner('Analyzing data...'):
                weekly_sales_analysis(filtered_data, selected_categories_sidebar, top_categories, selected_categories, start_date, end_date)
                hourly_sales_analysis(filtered_data, selected_categories, selected_categories_sidebar)
                profit_margin_analysis(filtered_data, selected_categories, selected_categories_sidebar)

                if selected_categories_sidebar:
                    category_performance_analysis(filtered_data, selected_categories, selected_stores)
                    daily_sales_analysis(filtered_data, selected_categories, selected_stores)
                    store_performance_analysis(data, filtered_data, selected_categories, selected_stores)
                    category_breakdown_analysis(filtered_data, selected_categories)
                    top_products_analysis(filtered_data, selected_categories)
                    category_comparison_analysis(filtered_data, selected_categories)
        except Exception as e:
            st.error(f"An error occurred during analysis: {str(e)}")
            st.exception(e)
    else:
        st.warning("No data found for the selected criteria.")
else:
    st.warning("No data available. Please ensure the data directory is correctly configured.")
