import streamlit as st
import pandas as pd
import plotly.express as px

def profit_margin_analysis(filtered_data):
    st.markdown("<h1 style='text-align: center; color: green;'>Profit Analysis</h1>", unsafe_allow_html=True)

    # Ensure numeric conversion for analysis
    filtered_data['sellingPrice'] = pd.to_numeric(filtered_data['sellingPrice'], errors='coerce')
    filtered_data['costPrice'] = pd.to_numeric(filtered_data['costPrice'], errors='coerce')
    filtered_data['quantity'] = pd.to_numeric(filtered_data['quantity'], errors='coerce')

    # Get unique brands available in the selected data
    unique_brands_in_selected_stores = filtered_data['brandName'].unique().tolist()

    # Sidebar brand selector
    with st.sidebar:
        selected_brands = st.multiselect(
            "Select Brands for Analysis", 
            options=unique_brands_in_selected_stores, 
            default=[], 
            key="brand_selector_profit" 
        )

    # Default to all brands if none are selected
    if not selected_brands:
        selected_brands = unique_brands_in_selected_stores

    # Filter data for selected brands
    filtered_data_brands = filtered_data[filtered_data['brandName'].isin(selected_brands)]

    # Compute aggregated metrics
    filtered_data_brands['total_sellingPrice'] = filtered_data_brands['sellingPrice'] * filtered_data_brands['quantity']
    filtered_data_brands['total_costPrice'] = filtered_data_brands['costPrice'] * filtered_data_brands['quantity']
    filtered_data_brands['profit'] = filtered_data_brands['total_sellingPrice'] - filtered_data_brands['total_costPrice']

    # Group by store and calculate profit metrics
    store_grouped = (filtered_data_brands.groupby('storeName')
                     .agg({'total_sellingPrice': 'sum', 'total_costPrice': 'sum', 'profit': 'sum'}))
    store_grouped = store_grouped.reset_index()
    store_grouped['avg_profit_margin'] = ((store_grouped['total_sellingPrice'] - store_grouped['total_costPrice']) / 
                                           store_grouped['total_sellingPrice']) * 100

    # Group by brand and calculate profit metrics
    product_grouped = (filtered_data_brands.groupby('brandName')
                       .agg({'total_sellingPrice': 'sum', 'total_costPrice': 'sum', 'profit': 'sum', 'quantity': 'sum'}))
    product_grouped = product_grouped.reset_index()
    product_grouped['avg_profit_margin'] = ((product_grouped['total_sellingPrice'] - product_grouped['total_costPrice']) / 
                                            product_grouped['total_sellingPrice']) * 100

    # Display store-level profit analysis
    st.dataframe(store_grouped)

    # Display product-grouped data only when specific brands are selected
    if selected_brands and set(selected_brands) != set(unique_brands_in_selected_stores):
        st.markdown("<h4 style='text-align: center; color: green;'>Profit Data by Selected Brands</h4>", unsafe_allow_html=True)
        st.dataframe(product_grouped)

    # Display store comparison profit chart
    st.markdown("<h4 style='text-align: center; color: green;'>Store Comparison Profit Chart</h4>", unsafe_allow_html=True)
    store_grouped_sorted = store_grouped.sort_values(by='profit', ascending=False)

    store_comparison_fig = px.bar(
        store_grouped_sorted, 
        x='storeName', 
        y='profit',
        title="Total Profit Comparison by Store",
        labels={'profit': 'Total Profit'},
        color='storeName', 
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    st.plotly_chart(store_comparison_fig, use_container_width=True)
