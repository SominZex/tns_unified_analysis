import streamlit as st
import pandas as pd
from utils.data_loader import load_data_from_directory
from brand_analysis.analysis.weekly_sales import weekly_sales_analysis
from brand_analysis.analysis.store_performance_analysis import store_performance_analysis
from brand_analysis.analysis.hourly_sales import hourly_sales_analysis
from brand_analysis.analysis.category_breakdown import category_breakdown_analysis
from brand_analysis.analysis.profit_margin_analysis import profit_margin_analysis
from brand_analysis.analysis.top_products import top_products_analysis
from brand_analysis.analysis.brand_comparison import brand_comparison_analysis
from brand_analysis.analysis.brand_performance_analysis import brand_performance_analysis
from brand_analysis.analysis.daily_sales_analysis import daily_sales_analysis

@st.cache_data
def load_optimized_data_from_directory():
    return load_data_from_directory() 

def filter_data(_data, brands, stores, start_date, end_date):
    if start_date is not None:
        start_date = pd.to_datetime(start_date, utc=True)
    if end_date is not None:
        end_date = pd.to_datetime(end_date, utc=True)

    _data['orderDate'] = pd.to_datetime(_data['orderDate'], utc=True)
    
    mask = (_data['orderDate'] >= start_date) & (_data['orderDate'] <= end_date) & \
           (_data['brandName'].isin(brands)) & (_data['storeName'].isin(stores))
    filtered_data = _data[mask]
    
    return filtered_data

def filter_data_by_date(_data, start_date, end_date):
    if start_date is not None:
        start_date = pd.to_datetime(start_date, utc=True)
    if end_date is not None:
        end_date = pd.to_datetime(end_date, utc=True)

    _data['orderDate'] = pd.to_datetime(_data['orderDate'], utc=True)
    
    mask = (_data['orderDate'] >= start_date) & (_data['orderDate'] <= end_date)
    date_filtered_data = _data[mask]
    
    brand_aggregated = date_filtered_data.groupby('brandName').agg(
        total_sales=('sellingPrice', lambda x: (x * date_filtered_data.loc[x.index, 'quantity']).sum()),
        total_cost=('costPrice', lambda x: (x * date_filtered_data.loc[x.index, 'quantity']).sum()),
        total_quantity=('quantity', 'sum')
    ).reset_index()
    
    brand_aggregated['profit'] = brand_aggregated['total_sales'] - brand_aggregated['total_cost']
    brand_aggregated['profit_margin'] = (brand_aggregated['profit'] / brand_aggregated['total_sales']) * 100
    
    return date_filtered_data, brand_aggregated


def get_top_brands(data, n=10):
    return data['brandName'].value_counts().head(n).index.tolist()

def get_top_stores(data, n=10):
    return data['storeName'].value_counts().head(n).index.tolist()

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
    st.session_state.last_upload = None

# Sidebar layout
with st.sidebar:
    with st.spinner('Loading data...'):
        # data = st.session_state = 
        st.session_state.data = load_optimized_data_from_directory()

    data = st.session_state.data

    if data is not None:  
        min_date = data['orderDate'].min()
        max_date = data['orderDate'].max()
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", min_date)
        with col2:
            end_date = st.date_input("End Date", max_date)
        
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        
        unique_brands = data['brandName'].unique()
        n_brands_available = len(unique_brands)

        n_brands = st.number_input(
            "Select number of top brands to analyze", 
            min_value=1, 
            max_value=n_brands_available, 
            value=min(250, n_brands_available),
            step=1
        )
 
        top_brands = get_top_brands(data, n=n_brands)
        
        selected_brands_sidebar = st.multiselect(
            "Select brands for analysis", 
            options=top_brands
        )
        
        unique_stores = data['storeName'].unique()
        n_stores_available = len(unique_stores)

        top_stores = get_top_stores(data, n=n_stores_available)
        
        selected_stores_sidebar = st.multiselect(
            "Select stores for analysis", 
            options=top_stores
        )
    else:
        st.warning("No Data found")

if data is not None:
    selected_brands = selected_brands_sidebar if selected_brands_sidebar else top_brands
    selected_stores = selected_stores_sidebar if selected_stores_sidebar else top_stores
    

    filtered_data = filter_data(data, selected_brands, selected_stores, start_date, end_date)
    
    date_filtered_data, brand_aggregated = filter_data_by_date(data, start_date, end_date)

    
    try:
        with st.spinner('Analyzing data...'):
            if len(filtered_data) > 0:

                overall_analysis = filtered_data.groupby('brandName').agg(
                    total_sales=('sellingPrice', lambda x: (x * filtered_data.loc[x.index, 'quantity']).sum()),
                    total_cost=('costPrice', lambda x: (x * filtered_data.loc[x.index, 'quantity']).sum()),
                    total_quantity=('quantity', 'sum')
                ).reset_index()

                overall_analysis['profit'] = overall_analysis['total_sales'] - overall_analysis['total_cost']

                brand_performance_analysis(date_filtered_data, selected_brands, selected_stores, selected_brands_sidebar)
                weekly_sales_analysis(filtered_data, selected_brands_sidebar, top_brands)
                daily_sales_analysis(filtered_data, selected_brands, selected_stores, selected_brands_sidebar)
                store_performance_analysis(data, date_filtered_data, selected_brands, selected_stores)
                hourly_sales_analysis(filtered_data, selected_brands, selected_brands_sidebar)

                if selected_brands_sidebar:
                    category_breakdown_analysis(filtered_data, selected_brands)
                    top_products_analysis(filtered_data, selected_brands)

                profit_margin_analysis(filtered_data, selected_brands, selected_brands_sidebar)
                

            else:
                st.warning("No data found for the selected criteria.")
    except Exception as e:
        st.error(f"An error occurred during analysis: {str(e)}")
        st.exception(e)
else:
    st.warning("Please upload a CSV file to begin analysis.")
