import pandas as pd
import plotly.express as px
import streamlit as st

def daily_sales_analysis(filtered_data, selected_products, selected_stores):
    st.markdown("<h1 style='text-align: center; color: green;'>Daily Sales</h1>", unsafe_allow_html=True)
    
    # Filter data based on selected products (formerly categories)
    daily_sales_data = filtered_data[filtered_data['productName'].isin(selected_products)]
    
    # Aggregate daily sales for each product
    daily_sales_data['orderDate'] = pd.to_datetime(daily_sales_data['orderDate'])
    daily_sales = daily_sales_data.groupby([daily_sales_data['orderDate'].dt.date, 'productName']).agg(
        total_sales=('sellingPrice', lambda x: (x * daily_sales_data.loc[x.index, 'quantity']).sum()),
        total_quantity=('quantity', 'sum'),
        total_cost=('costPrice', lambda x: (x * daily_sales_data.loc[x.index, 'quantity']).sum())
    ).reset_index()

    # Add profit calculation: total sales minus total cost
    daily_sales['profit'] = daily_sales['total_sales'] - daily_sales['total_cost']

    # Create a chart of daily sales
    chart_type = st.selectbox("Select chart type for Daily Sales", ["Line Chart", "Bar Chart", "Area Chart", "Donut Chart"])
    
    # Color palette for diverse and vibrant charts
    color_palette = px.colors.qualitative.Set2 

    if chart_type == "Line Chart":
        fig = px.line(daily_sales, x='orderDate', y='total_sales', color='productName', title="Daily Sales", color_discrete_sequence=color_palette)
    elif chart_type == "Bar Chart":
        fig = px.bar(daily_sales, x='orderDate', y='total_sales', color='productName', title="Daily Sales", color_discrete_sequence=color_palette)
    elif chart_type == "Area Chart":
        fig = px.area(daily_sales, x='orderDate', y='total_sales', color='productName', title="Daily Sales", color_discrete_sequence=color_palette)
    elif chart_type == "Donut Chart":
        fig = px.pie(daily_sales, names='productName', values='total_sales', title="Total Daily Sales per Product", hole=0.3, color_discrete_sequence=color_palette)

    # Update x-axis to show all dates without intervals
    fig.update_layout(
        xaxis=dict(
            tickmode='linear', 
            dtick="D1",
            tickformat="%Y-%m-%d",
        )
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # Display DataFrame summary
    st.dataframe(daily_sales)

    # Calculate metrics
    total_sales = daily_sales['total_sales'].sum()
    total_quantity = daily_sales['total_quantity'].sum()
    total_profit = daily_sales['profit'].sum()

    # Using st.columns() to display metrics side by side
    col1, col2, col3 = st.columns(3)

    # Display metrics in each column
    with col1:
        st.metric("Total Sales", f"₹{total_sales:,.2f}")
    with col2:
        st.metric("Total Quantity Sold", f"{total_quantity:,.0f}")
    with col3:
        st.metric("Total Profit", f"₹{total_profit:,.2f}")
