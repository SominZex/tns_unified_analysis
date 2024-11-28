import streamlit as st
import pandas as pd
import plotly.express as px

def profit_margin_analysis(filtered_data):
    st.markdown("<h1 style='text-align: center; color: green;'>Profit Analysis</h1>", unsafe_allow_html=True)

    # Ensure sellingPrice, costPrice, and quantity are numeric
    filtered_data['sellingPrice'] = pd.to_numeric(filtered_data['sellingPrice'], errors='coerce')
    filtered_data['costPrice'] = pd.to_numeric(filtered_data['costPrice'], errors='coerce')
    filtered_data['quantity'] = pd.to_numeric(filtered_data['quantity'], errors='coerce')

    # Get unique brands from the filtered data
    unique_brands_in_selected_stores = filtered_data['brandName'].unique().tolist()

    # Add a brand selector (multiselect) to let the user choose specific brands
    selected_brands = st.multiselect(
        "Select Brands for Analysis", options=unique_brands_in_selected_stores, default=[]
    )

    # If no brands are selected, use all brands
    if not selected_brands:
        selected_brands = unique_brands_in_selected_stores

    # Filter the data to include only selected brands
    filtered_data_brands = filtered_data[filtered_data['brandName'].isin(selected_brands)]

    # Calculate total selling price and total cost price by multiplying by quantity (after filtering)
    filtered_data_brands['total_sellingPrice'] = filtered_data_brands['sellingPrice'] * filtered_data_brands['quantity']
    filtered_data_brands['total_costPrice'] = filtered_data_brands['costPrice'] * filtered_data_brands['quantity']

    # Calculate profit column for filtered data
    filtered_data_brands['profit'] = filtered_data_brands['total_sellingPrice'] - filtered_data_brands['total_costPrice']

    # Group by store and sum the total sellingPrice, total costPrice, and profit
    store_grouped = (filtered_data_brands.groupby('storeName')
                     .agg({'total_sellingPrice': 'sum', 'total_costPrice': 'sum', 'profit': 'sum'}))
    store_grouped = store_grouped.reset_index()

    # Calculate average profit margin based on summed values
    store_grouped['avg_profit_margin'] = ((store_grouped['total_sellingPrice'] - store_grouped['total_costPrice']) / 
                                           store_grouped['total_sellingPrice']) * 100

    # Group the filtered data by brandName and calculate total sales, total cost, and profit
    product_grouped = (filtered_data_brands.groupby('brandName')
                       .agg({'total_sellingPrice': 'sum', 'total_costPrice': 'sum', 'profit': 'sum', 'quantity': 'sum'}))
    product_grouped = product_grouped.reset_index()

    # Calculate the average profit margin for each brand
    product_grouped['avg_profit_margin'] = ((product_grouped['total_sellingPrice'] - product_grouped['total_costPrice']) / 
                                            product_grouped['total_sellingPrice']) * 100

    # Display data table with all required features, including total_sellingPrice, total_costPrice, profit
    st.dataframe(store_grouped)

    # Display the selected brands' table
    st.markdown("<h4 style='text-align: center; color: green;'>Profit Data by Selected Brands</h4>", unsafe_allow_html=True)
    st.dataframe(product_grouped)

    # Store Comparison Profit Chart (updated to plot profit instead of sales)
    st.markdown("<h4 style='text-align: center; color: green;'>Store Comparison Profit Chart</h4>", unsafe_allow_html=True)
    store_comparison_fig = px.bar(
        store_grouped, 
        x='storeName', 
        y='profit',
        title="Total Profit Comparison by Store",
        labels={'profit': 'Total Profit'},
        color='storeName', 
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(store_comparison_fig, use_container_width=True)

    # Sidebar options for chart customization (optional)
    # st.sidebar.subheader("Profit Margin Chart Settings")
    
    # Chart rendering for profit margin (optional)
    # chart_type = st.selectbox("Select Chart Type", ["Bar Chart", "Scatter Plot"], key="profit_margin_chart_type")
    # show_data_labels = st.checkbox("Show Data Labels", False, key="profit_margin_show_data_labels")
    
    # if chart_type == "Bar Chart":
    #     fig = px.bar(store_grouped, x='storeName', y='avg_profit_margin', title="Average Profit Margin by Store",
    #                  labels={'avg_profit_margin': 'Profit Margin (%)'}, color='storeName', color_discrete_sequence=px.colors.qualitative.Set3)
        
    #     if show_data_labels:
    #         fig.update_traces(text=store_grouped['avg_profit_margin'].round(2), textposition="inside")
            
    # elif chart_type == "Scatter Plot":
    #     fig = px.scatter(store_grouped, x='storeName', y='avg_profit_margin', title="Profit Margin by Store",
    #                      labels={'avg_profit_margin': 'Profit Margin (%)'}, color='storeName', color_discrete_sequence=px.colors.qualitative.Set3)

    #     if show_data_labels:
    #         fig.update_traces(text=store_grouped['avg_profit_margin'].round(2), textposition="top center")

    # st.plotly_chart(fig, use_container_width=True)
