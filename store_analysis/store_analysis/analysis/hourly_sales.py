import streamlit as st
import pandas as pd
import plotly.express as px

def hourly_sales_analysis(filtered_data, selected_stores, selected_stores_sidebar):
    st.markdown("<h1 style='text-align: center; color: green;'>Hourly Sales</h1>", unsafe_allow_html=True)

    # If no stores are selected, use all unique stores
    if selected_stores is None:
        selected_stores = filtered_data['storeName'].unique()

    # Filter data for selected stores
    filtered_data = filtered_data[filtered_data['storeName'].isin(selected_stores)]
    
    # Ensure the 'time' column is a datetime type
    filtered_data['time'] = pd.to_datetime(filtered_data['time'], errors='coerce') 

    # Extract hour from the time column and calculate total selling price and cost price
    filtered_data['hour'] = filtered_data['time'].apply(lambda x: x.hour if pd.notnull(x) else None)
    filtered_data['total_selling_price'] = filtered_data['sellingPrice'] * filtered_data['quantity']
    filtered_data['total_cost_price'] = filtered_data['costPrice'] * filtered_data['quantity']
    
    # Aggregating sales by each hour (creating 24 columns for each hour)
    hourly_sales = filtered_data.pivot_table(
        index='storeName', 
        columns='hour', 
        values='total_selling_price', 
        aggfunc='sum', 
        fill_value=0
    ).reset_index()

    # Display store-wise data table (with 24 columns representing each hour)
    st.dataframe(hourly_sales)

    if selected_stores_sidebar:
        # Sidebar options for store-wise chart
        st.sidebar.subheader("Store-wise Hourly Sales Chart Settings")
        
        chart_type_stores = st.sidebar.selectbox(
            "Select Chart Type (Store-wise)", 
            ["Line Chart", "Bar Chart", "Area Chart"], 
            key="hourly_sales_chart_type_stores"
        )
        
        show_data_labels_stores = st.sidebar.checkbox(
            "Show Data Labels (Store-wise)", 
            False, 
            key="hourly_sales_show_data_labels_stores"
        )
        
        # Reshaping the data for plotting (long format)
        hourly_sales_long = hourly_sales.melt(id_vars='storeName', 
                                            value_vars=hourly_sales.columns[1:], 
                                            var_name='hour', 
                                            value_name='total_selling_price')
        
        # Chart rendering for store-wise analysis
        if chart_type_stores == "Line Chart":
            fig_stores = px.line(hourly_sales_long, x='hour', y='total_selling_price', color='storeName',
                                title="Store-wise Hourly Sales",
                                labels={'total_selling_price': 'Total Sales', 'hour': 'Hour'})
        elif chart_type_stores == "Bar Chart":
            fig_stores = px.bar(hourly_sales_long, x='hour', y='total_selling_price', color='storeName',
                                title="Store-wise Hourly Sales",
                                labels={'total_selling_price': 'Total Sales', 'hour': 'Hour'})
        else:
            fig_stores = px.area(hourly_sales_long, x='hour', y='total_selling_price', color='storeName',
                                title="Store-wise Hourly Sales",
                                labels={'total_selling_price': 'Total Sales', 'hour': 'Hour'})
        
        # Ensure all hours (0-23) are on the x-axis
        fig_stores.update_xaxes(range=[0, 23], tickmode='linear', tick0=0, dtick=1)
        
        if show_data_labels_stores:
            fig_stores.update_traces(textposition="top center")
        
        # Display the Store-wise Hourly Sales chart
        st.plotly_chart(fig_stores, use_container_width=True)

        # Aggregated Hourly Sales Analysis (with 24 columns for total sales)
        st.subheader("Total Hourly Sales")

        # Aggregated hourly sales data (with 24 columns for each hour)
        total_hourly_sales = filtered_data.groupby('hour').agg(
            total_selling_price=('total_selling_price', 'sum'),
            total_cost_price=('total_cost_price', 'sum'),
            quantity=('quantity', 'sum')
        ).reset_index()

        # Display aggregated data table (with 24 columns representing each hour)
        st.dataframe(total_hourly_sales)
