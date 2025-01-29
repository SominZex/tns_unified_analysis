import streamlit as st
import pandas as pd
import plotly.express as px

def brand_performance_analysis(filtered_data, date_filtered, selected_stores):
    st.markdown("<h1 style='text-align: center; color: green;'>Brand Comparison by Stores</h1>", unsafe_allow_html=True)

    # Calculate total selling price to determine top brands by sales
    filtered_data['total_selling_price'] = filtered_data['sellingPrice'] * filtered_data['quantity']
    top_brands_data = (
        filtered_data.groupby('brandName', as_index=False)
        .agg(total_sales=('total_selling_price', 'sum'))
        .sort_values(by='total_sales', ascending=False)
    )

    # Move brand selector to the sidebar
    selected_brands = st.sidebar.multiselect(
        "Select Brands for Comparison",
        options=top_brands_data['brandName'].tolist(),
        default=[],
        key="brand_selector"
    )

    # If no brands are selected, use all brands in the filtered data for the analysis
    if not selected_brands:
        selected_brands = top_brands_data['brandName'].tolist()

    # Filter data for selected brands and stores
    filtered_data = filtered_data[filtered_data['brandName'].isin(selected_brands) & filtered_data['storeName'].isin(selected_stores)]

    # Calculate total cost price for the filtered data
    filtered_data['total_cost_price'] = filtered_data['costPrice'] * filtered_data['quantity']

    # Calculate overall total sales and profit based on the filtered data
    overall_total_selling_price = filtered_data['total_selling_price'].sum()
    overall_total_cost_price = filtered_data['total_cost_price'].sum()
    overall_profit = overall_total_selling_price - overall_total_cost_price

    # Aggregate the data based on each unique storeName
    aggregated_data = (
        filtered_data.groupby('storeName', as_index=False)
        .agg(
            total_selling_price=('total_selling_price', 'sum'),
            total_cost_price=('total_cost_price', 'sum'),
            total_quantity=('quantity', 'sum'),
            category_count=('categoryName', 'nunique')
        )
        .sort_values(by='total_selling_price', ascending=False)
    )

    # Calculate profit and add it to the aggregated data
    aggregated_data['profit'] = aggregated_data['total_selling_price'] - aggregated_data['total_cost_price']
    
    # # Calculate contribution percentages based on overall totals
    # aggregated_data['sales_contribution'] = (aggregated_data['total_selling_price'] / overall_total_selling_price) * 100
    # aggregated_data['profit_contribution'] = (aggregated_data['profit'] / overall_profit) * 100
    
    # # Format contribution percentages for better readability
    # aggregated_data['sales_contribution'] = aggregated_data['sales_contribution'].apply(lambda x: f"{x:.2f}%")
    # aggregated_data['profit_contribution'] = aggregated_data['profit_contribution'].apply(lambda x: f"{x:.2f}%")

    # Chart options for customization in the sidebar
    chart_type = st.sidebar.selectbox("Select Chart Type", ["Bar Chart", "Line Chart", "Area Chart"], key="chart_type_selector")
    show_data_labels = st.sidebar.checkbox("Show Data Labels", value=False, key="show_data_labels_checkbox")

    # Generate the Plotly chart based on selected options
    if chart_type == "Bar Chart":
        fig = px.bar(
            aggregated_data,
            x="storeName",
            y="total_selling_price",
            title="Total Sales by Store",
            color="storeName",
            color_discrete_sequence=px.colors.qualitative.Set1,
            text="total_selling_price" if show_data_labels else None
        )
    elif chart_type == "Line Chart":
        fig = px.line(
            aggregated_data,
            x="storeName",
            y="total_selling_price",
            title="Total Sales by Store",
            markers=True,
            line_shape='linear',
            color_discrete_sequence=["green"],
        )
        if show_data_labels:
            fig.update_traces(text=aggregated_data['total_selling_price'], textposition="top center")
    elif chart_type == "Area Chart":
        fig = px.area(
            aggregated_data,
            x="storeName",
            y="total_selling_price",
            title="Total Sales by Store",
            color="storeName", 
            color_discrete_sequence=px.colors.qualitative.Set1,
        )
        if show_data_labels:
            fig.update_traces(text=aggregated_data['total_selling_price'], textposition="top center")

    # Configure the chart layout for better visuals
    fig.update_layout(
        xaxis_title="Store",
        yaxis_title="Total Sales",
        hovermode="x unified",
        showlegend=True 
    )

    # Display the Plotly chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<h4 style='text-align: center; color: green;'>Selected Brand Dataframe</h4>", unsafe_allow_html=True)

    # Display the aggregated data with contribution percentages
    st.write(aggregated_data)
