import streamlit as st
import pandas as pd
import plotly.express as px

def brand_performance_analysis(filtered_data, selected_brands, selected_stores, selected_brands_sidebar):
    st.markdown("<h1 style='text-align: center; color: green;'>Brand Performance Analysis</h1>", unsafe_allow_html=True)

    # Calculate total selling and cost prices for the filtered data
    filtered_data['total_selling_price'] = filtered_data['sellingPrice'] * filtered_data['quantity']
    filtered_data['total_cost_price'] = filtered_data['costPrice'] * filtered_data['quantity']

    # Calculate overall total sales and profit based on the filtered data
    overall_total_selling_price = filtered_data['total_selling_price'].sum()
    overall_total_cost_price = filtered_data['total_cost_price'].sum()
    overall_profit = overall_total_selling_price - overall_total_cost_price

    # Filter data for selected brands and stores
    filtered_data = filtered_data[filtered_data['brandName'].isin(selected_brands) & filtered_data['storeName'].isin(selected_stores)]

    # Aggregate the data based on each unique brandName
    aggregated_data = (
        filtered_data.groupby('brandName', as_index=False)
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
    
    # Calculate profit margin and format it as a percentage
    aggregated_data['profit_margin'] = (aggregated_data['profit'] / aggregated_data['total_selling_price']) * 100
    aggregated_data['profit_margin'] = aggregated_data['profit_margin'].apply(lambda x: f"{x:.2f}%")

    # Calculate contribution percentages based on overall totals
    aggregated_data['sales_contribution'] = (aggregated_data['total_selling_price'] / overall_total_selling_price) * 100
    aggregated_data['profit_contribution'] = (aggregated_data['profit'] / overall_profit) * 100
    
    # Format contribution percentages for better readability
    aggregated_data['sales_contribution'] = aggregated_data['sales_contribution'].apply(lambda x: f"{x:.2f}%")
    aggregated_data['profit_contribution'] = aggregated_data['profit_contribution'].apply(lambda x: f"{x:.2f}%")

    if selected_brands_sidebar:
        # Chart options for customization in the sidebar
        chart_type = st.sidebar.selectbox("Select Chart Type", ["Bar Chart", "Line Chart", "Area Chart"], key="chart_type_selector")
        show_data_labels = st.sidebar.checkbox("Show Data Labels", value=False, key="show_data_labels_checkbox")

        # Generate the Plotly chart based on selected options
        if chart_type == "Bar Chart":
            fig = px.bar(
                aggregated_data,
                x="brandName",
                y="total_selling_price",
                title="Total Sales by Brand",
                color="brandName",
                color_discrete_sequence=px.colors.qualitative.Set1,
                text="total_selling_price" if show_data_labels else None
            )
        elif chart_type == "Line Chart":
            fig = px.line(
                aggregated_data,
                x="brandName",
                y="total_selling_price",
                title="Total Sales by Brand",
                markers=True,
                line_shape='linear',
                color_discrete_sequence=["green"],
            )
            if show_data_labels:
                fig.update_traces(text=aggregated_data['total_selling_price'], textposition="top center")
        elif chart_type == "Area Chart":
            fig = px.area(
                aggregated_data,
                x="brandName",
                y="total_selling_price",
                title="Total Sales by Brand",
                color="brandName", 
                color_discrete_sequence=px.colors.qualitative.Set1,
            )
            if show_data_labels:
                fig.update_traces(text=aggregated_data['total_selling_price'], textposition="top center")

        # Configure the chart layout for better visuals
        fig.update_layout(
            xaxis_title="Brand",
            yaxis_title="Total Sales",
            hovermode="x unified",
            showlegend=True 
        )

        # Display the Plotly chart in Streamlit
        st.plotly_chart(fig, use_container_width=True)


    # Display the aggregated data with contribution percentages
    st.write(aggregated_data)
