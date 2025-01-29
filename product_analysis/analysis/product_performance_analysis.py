import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

def product_performance_analysis(filtered_data, selected_products, selected_stores):
    st.markdown("<h1 style='text-align: center; color: blue;'>Product Performance Analysis</h1>", unsafe_allow_html=True)

    # Calculate total selling and cost prices
    filtered_data['total_selling_price'] = filtered_data['sellingPrice'] * filtered_data['quantity']
    filtered_data['total_cost_price'] = filtered_data['costPrice'] * filtered_data['quantity']

    # Filter data for selected products and stores
    filtered_data = filtered_data[
        filtered_data['productName'].isin(selected_products) & 
        filtered_data['storeName'].isin(selected_stores)
    ]

    if filtered_data.empty:
        st.warning("No data available for the selected products or stores. Please refine your selections.")
        return

    # Aggregate data without store_count
    aggregated_data = (
        filtered_data.groupby(['productName', 'storeName'], as_index=False)
        .agg(
            total_selling_price=('total_selling_price', 'sum'),
            total_cost_price=('total_cost_price', 'sum'),
            total_quantity=('quantity', 'sum')
        )
    )

    # Calculate store_count separately at the product level
    store_counts = (
        filtered_data.groupby('productName', as_index=False)
        .agg(store_count=('storeName', 'nunique'))
    )

    # Merge store_count into the aggregated data
    aggregated_data = aggregated_data.merge(store_counts, on='productName', how='left')


    # Calculate profit
    aggregated_data['profit'] = aggregated_data['total_selling_price'] - aggregated_data['total_cost_price']

    aggregated_data['profit_margin'] = np.where(
        aggregated_data['total_selling_price'] != 0,
        (aggregated_data['profit'] / aggregated_data['total_selling_price']) * 100,
        0
    )
    # Overall totals
    overall_total_selling_price = filtered_data['total_selling_price'].sum()
    overall_profit = aggregated_data['profit'].sum()

    if overall_total_selling_price == 0 or overall_profit == 0:
        st.warning("Overall totals are zero, contributions cannot be calculated.")
        return

    # Contribution percentages
    aggregated_data['sales_contribution'] = np.where(
        overall_total_selling_price != 0,
        (aggregated_data['total_selling_price'] / overall_total_selling_price) * 100,
        0
    )
    aggregated_data['profit_contribution'] = np.where(
        overall_profit != 0,
        (aggregated_data['profit'] / overall_profit) * 100,
        0
    )

    aggregated_data.reset_index(drop=True, inplace=True)

    # Format percentages
    aggregated_data['profit_margin'] = aggregated_data['profit_margin'].apply(lambda x: f"{x:.2f}%")
    aggregated_data['sales_contribution'] = aggregated_data['sales_contribution'].apply(lambda x: f"{x:.2f}%")
    aggregated_data['profit_contribution'] = aggregated_data['profit_contribution'].apply(lambda x: f"{x:.2f}%")


    # Chart options for customization in the sidebar
    chart_type = st.sidebar.selectbox("Select Chart Type", ["Bar Chart", "Line Chart", "Area Chart"], key="chart_type_selector")
    show_data_labels = st.sidebar.checkbox("Show Data Labels", value=False, key="show_data_labels_checkbox")

    # Generate the Plotly chart based on selected options
    if chart_type == "Bar Chart":
        fig = px.bar(
            aggregated_data,
            x="productName",
            y="total_selling_price",
            title="Total Sales by Product and Store",
            color="storeName",
            color_discrete_sequence=px.colors.qualitative.Set1,
            text="total_selling_price" if show_data_labels else None
        )
    elif chart_type == "Line Chart":
        fig = px.line(
            aggregated_data,
            x="productName",
            y="total_selling_price",
            title="Total Sales by Product and Store",
            markers=True,
            line_shape='linear',
            color_discrete_sequence=["green"],
        )
        if show_data_labels:
            fig.update_traces(text=aggregated_data['total_selling_price'], textposition="top center")
    elif chart_type == "Area Chart":
        fig = px.area(
            aggregated_data,
            x="productName",
            y="total_selling_price",
            title="Total Sales by Product and Store",
            color="storeName", 
            color_discrete_sequence=px.colors.qualitative.Set1,
        )
        if show_data_labels:
            fig.update_traces(text=aggregated_data['total_selling_price'], textposition="top center")

    # Configure the chart layout for better visuals
    fig.update_layout(
        xaxis_title="Product",
        yaxis_title="Total Sales",
        hovermode="x unified",
        showlegend=True 
    )

    # Display the Plotly chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<h4 style='text-align: center; color: blue;'>Selected Product and Store Dataframe</h4>", unsafe_allow_html=True)

    # Display the aggregated data with contribution percentages
    st.write(aggregated_data)
