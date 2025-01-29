import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


def weekly_sales_analysis(data, selected_product_sidebar, top_products):
    st.markdown("<h1 style='text-align: center; color: green;'>Weekly Sales by Product</h1>", unsafe_allow_html=True)

    # Ensure that data is available
    if data is None:
        st.warning("Please upload data.")
        return

    # Filter data for the selected products (sidebar filter)
    if len(selected_product_sidebar) > 0:
        filtered_data = data[data['productName'].isin(selected_product_sidebar)]
    else:
        # Show all data if no products are selected, but limit to top products if necessary
        filtered_data = data[data['productName'].isin(top_products)]

    # Check if filtered data is empty
    if filtered_data.empty:
        st.warning("No sales data available for the selected products.")
        return

    # Ensure that the orderDate column is in datetime format
    filtered_data['orderDate'] = pd.to_datetime(filtered_data['orderDate'], errors='coerce')

    # Extract the day of the week and month from orderDate
    filtered_data['day'] = filtered_data['orderDate'].dt.day_name()
    filtered_data['month'] = filtered_data['orderDate'].dt.month_name()

    # Calculate total selling price by multiplying sellingPrice with quantity
    filtered_data['total_selling_price'] = filtered_data['sellingPrice'] * filtered_data['quantity']
    filtered_data['total_cost_price'] = filtered_data['costPrice'] * filtered_data['quantity']

    # Aggregate sales data based on unique productName, month, and day of the week
    weekly_sales = (
        filtered_data.groupby(['month', 'productName', 'day'], as_index=False)
        .agg(
            total_selling_price=('total_selling_price', 'sum'),
            total_cost_price=('total_cost_price', 'sum'),
            total_quantity=('quantity', 'sum'),
            brand_count=('brandName', 'nunique')
        )
        .sort_values(by=['month', 'day'])
    )

    # Aggregate sales data based on product, month, and dynamic week label
    filtered_data['month_year'] = filtered_data['orderDate'].dt.to_period('M')  
    filtered_data['week_number'] = filtered_data.groupby('month_year')['orderDate'].transform(
        lambda x: (x.dt.day - 1) // 7 + 1 
    )

    filtered_data['week_label'] = 'Week ' + filtered_data['week_number'].astype(str)

    # Ensure no duplication by filtering based on month and week_label combination
    weekly_sales_by_week = (
        filtered_data.groupby(['month', 'productName', 'week_label'], as_index=False)
        .agg(
            total_selling_price=('total_selling_price', 'sum'),
            total_cost_price=('total_cost_price', 'sum'),
            total_quantity=('quantity', 'sum'),
            brand_count=('brandName', 'nunique')
        )
        .sort_values(by=['month', 'week_label'])
    )

    # Pivot the DataFrame to create separate columns for each week label
    sales_by_week = weekly_sales_by_week.pivot_table(
        index=['month', 'productName'],
        columns='week_label',
        values='total_selling_price',
        fill_value=0
    ).reset_index()

    # Calculate weekly sales growth percentage
    sales_by_week_growth = sales_by_week.copy()
    week_columns = sales_by_week.columns[2:]

    # Calculate percentage growth for each week column relative to the previous week
    for i in range(1, len(week_columns)):
        week, prev_week = week_columns[i], week_columns[i - 1]
        prev_week_sales = sales_by_week[prev_week]
        growth = np.where(
            prev_week_sales != 0,
            ((sales_by_week[week] - prev_week_sales) / prev_week_sales) * 100,
            0 
        )
        sales_by_week_growth[f"{week}_growth"] = growth

    # Calculate average growth
    available_growth_columns = [col for col in sales_by_week_growth.columns if col.endswith('_growth')]
    if available_growth_columns:
        sales_by_week_growth['avg_growth'] = sales_by_week_growth[available_growth_columns].mean(axis=1).round(2)
    else:
        sales_by_week_growth['avg_growth'] = 0

    # Move 'month' column before 'productName'
    sales_by_week_growth = sales_by_week_growth[['month', 'productName'] + [col for col in sales_by_week_growth.columns if col not in ['month', 'productName']]]

    # Create a styled DataFrame for display
    def style_negative_red_positive_green(val):
        if isinstance(val, (int, float)):
            color = 'red' if val < 0 else 'green'
            return f'color: {color}'
        return ''

    # Format the growth percentage columns
    growth_columns = [col for col in sales_by_week_growth.columns if 'growth' in col]
    week_columns = [col for col in sales_by_week_growth.columns if col.startswith('Week') and not col.endswith('growth')]
    
    for col in growth_columns:
        sales_by_week_growth[col] = sales_by_week_growth[col].round(2)
    for col in week_columns:
        sales_by_week_growth[col] = sales_by_week_growth[col].round(2)

    # Create a styled DataFrame
    styled_df = sales_by_week_growth.style.applymap(
        style_negative_red_positive_green,
        subset=growth_columns
    ).format({
        **{col: "{:.2f}%" for col in growth_columns},
        **{col: "{:.2f}" for col in week_columns}
    })

    # Display the weekly sales with growth percentage
    st.markdown("<h4 style='text-align: center; color: green;'>Week-wise Sales with Growth Percentage</h4>", unsafe_allow_html=True)
    
    # Display the interactive dataframe with styling
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )


    if selected_product_sidebar:
        st.sidebar.subheader("Weekly Sales Chart Settings")
        chart_type = st.sidebar.selectbox(
            "Select Chart Type", 
            ["Line Chart", "Bar Chart", "Area Chart"], 
            index=1
        )
        color_scheme = px.colors.qualitative.Plotly
        
        # Ensure data is grouped by month and product to avoid extra lines
        if len(selected_product_sidebar) == 1:
            filtered_sales = weekly_sales_by_week[weekly_sales_by_week['productName'] == selected_product_sidebar[0]]
        else:
            filtered_sales = weekly_sales_by_week
        
        # Plot monthly sales data (grouped by week_label and month)
        if chart_type == "Line Chart":
            fig = px.line(
                filtered_sales,
                x='week_label',
                y='total_selling_price',
                color='productName',
                title="Monthly Sales Trend by Product",
                labels={'total_selling_price': 'Sales'},
                color_discrete_sequence=color_scheme
            )
            fig.update_xaxes(tickmode='array', tickvals=filtered_sales['week_label'].unique())
            fig.update_layout(xaxis_title="Month & Week", yaxis_title="Sales")
        elif chart_type == "Bar Chart":
            fig = px.bar(
                filtered_sales,
                x='week_label',
                y='total_selling_price',
                color='productName',
                title="Monthly Sales Trend by Product",
                labels={'total_selling_price': 'Sales'},
                color_discrete_sequence=color_scheme
            )
            fig.update_xaxes(tickmode='array', tickvals=filtered_sales['week_label'].unique())
            fig.update_layout(xaxis_title="Month & Week", yaxis_title="Sales")
        elif chart_type == "Area Chart":
            fig = px.area(
                filtered_sales,
                x='week_label',
                y='total_selling_price',
                color='productName',
                title="Monthly Sales Trend by Product",
                labels={'total_selling_price': 'Sales'},
                color_discrete_sequence=color_scheme
            )
            fig.update_xaxes(tickmode='array', tickvals=filtered_sales['week_label'].unique())
            fig.update_layout(xaxis_title="Month & Week", yaxis_title="Sales")


        st.plotly_chart(fig, use_container_width=True)
