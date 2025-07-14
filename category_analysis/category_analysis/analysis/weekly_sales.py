import pandas as pd
import plotly.express as px
import streamlit as st
import numpy as np

def weekly_sales_analysis(data, selected_categories_sidebar, top_categories, selected_categories, start_date, end_date):
    st.markdown("<h1 style='text-align: center; color: green;'>Weekly Sales</h1>", unsafe_allow_html=True)

    if data is None or (selected_categories_sidebar is None and top_categories is None):
        st.warning("Please upload data and select at least one category.")
        return

    if len(selected_categories_sidebar) > 0:
        data = data[data['categoryName'].isin(selected_categories_sidebar)]
    if top_categories:
        data = data[data['categoryName'].isin(top_categories)]

    if data.empty:
        st.warning("No sales data available for the selected categories.")
        return

    # Apply date range filtering
    data = data[(data['orderDate'] >= start_date) & (data['orderDate'] <= end_date)]

    # Add a dynamic month column for the selected date range
    data['month'] = data['orderDate'].dt.month_name()

    # Add total selling and cost price columns
    data['total_selling_price'] = data['sellingPrice'] * data['quantity']
    data['total_cost_price'] = data['costPrice'] * data['quantity']

    data['day'] = data['orderDate'].dt.day_name()
    # Grouping by month, category, and day for weekly sales data
    weekly_sales = (
        data.groupby(['month', 'categoryName', 'day'], as_index=False)
        .agg(
            total_selling_price=('total_selling_price', 'sum'),
            total_cost_price=('total_cost_price', 'sum'),
            total_quantity=('quantity', 'sum'),
            brand_count=('brandName', 'nunique')
        )
        .sort_values(by=['month', 'day'])
    )

    # Create dynamic month column for selected months
    selected_months = data['month'].unique()
    monthly_sales = weekly_sales[weekly_sales['month'].isin(selected_months)]

    sales_by_day = monthly_sales.groupby(['month', 'categoryName', 'day'])['total_selling_price'].sum().unstack(fill_value=0).reset_index()

    monthly_sales = monthly_sales[['month', 'categoryName', 'day', 'total_selling_price', 'total_cost_price', 'total_quantity', 'brand_count']]

    # Add week number and week label for further grouping
    data['month_year'] = data['orderDate'].dt.to_period('M') 
    data['week_number'] = data.groupby('month_year')['orderDate'].transform(
        lambda x: (x.dt.day - 1) // 7 + 1 
    )

    data['week_label'] = 'Week ' + data['week_number'].astype(str)

    # Group by week number for weekly sales analysis
    weekly_sales_by_week = (
        data.groupby(['month', 'categoryName', 'week_label'], as_index=False)
        .agg(
            total_selling_price=('total_selling_price', 'sum'),
            total_cost_price=('total_cost_price', 'sum'),
            total_quantity=('quantity', 'sum'),
            brand_count=('brandName', 'nunique')
        )
        .sort_values(by=['month', 'week_label'])
    )

    sales_by_week = weekly_sales_by_week.groupby(['month', 'categoryName', 'week_label'])['total_selling_price'].sum().unstack(fill_value=0).reset_index()

    # Calculate week-over-week growth
    sales_by_week_growth = sales_by_week.copy()
    week_columns = sales_by_week.columns[2:]

    for i in range(1, len(week_columns)):
        week, prev_week = week_columns[i], week_columns[i - 1]
        prev_week_sales = sales_by_week[prev_week]
        growth = np.where(
            prev_week_sales != 0,
            ((sales_by_week[week] - prev_week_sales) / prev_week_sales) * 100,
            0  
        )
        sales_by_week_growth[f"{week}_growth"] = growth

    available_growth_columns = [col for col in sales_by_week_growth.columns if col.endswith('_growth')]
    if available_growth_columns:
        sales_by_week_growth['avg_growth'] = sales_by_week_growth[available_growth_columns].mean(axis=1).round(2)
    else:
        sales_by_week_growth['avg_growth'] = 0

    def style_negative_red_positive_green(val):
        if isinstance(val, (int, float)):
            color = 'red' if val < 0 else 'green'
            return f'color: {color}'
        return ''

    growth_columns = [col for col in sales_by_week_growth.columns if 'growth' in col]
    week_columns = [col for col in sales_by_week_growth.columns if col.startswith('Week') and not col.endswith('growth')]

    for col in growth_columns:
        sales_by_week_growth[col] = sales_by_week_growth[col].round(2)
    for col in week_columns:
        sales_by_week_growth[col] = sales_by_week_growth[col].round(2)


    styled_df = sales_by_week_growth.style.applymap(
        style_negative_red_positive_green,
        subset=growth_columns
    ).format({
        **{col: "{:.2f}%" for col in growth_columns},
        **{col: "{:.2f}" for col in week_columns}
    })

    st.markdown("<h4 style='text-align: center; color: green;'>Week-wise Sales with Growth Percentage</h4>", unsafe_allow_html=True)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    if selected_categories_sidebar:
        st.sidebar.subheader("Weekly Sales Chart Settings")
        chart_type = st.sidebar.selectbox(
            "Select Chart Type", 
            ["Line Chart", "Bar Chart", "Area Chart", "Donut Chart"], 
            index=1
        )
        color_scheme = px.colors.qualitative.Plotly
    
        if chart_type == "Line Chart":
            fig = px.line(
                monthly_sales,
                x='day',
                y='total_selling_price',
                color='categoryName',
                title="Weekly Sales Trend",
                labels={'total_selling_price': 'Sales'},
                color_discrete_sequence=color_scheme
            )
        elif chart_type == "Bar Chart":
            fig = px.bar(
                monthly_sales,
                x='day',
                y='total_selling_price',
                color='categoryName',
                title="Weekly Sales Trend",
                labels={'total_selling_price': 'Sales'},
                color_discrete_sequence=color_scheme
            )
        elif chart_type == "Area Chart":
            fig = px.area(
                monthly_sales,
                x='day',
                y='total_selling_price',
                color='categoryName',
                title="Weekly Sales Trend",
                labels={'total_selling_price': 'Sales'},
                color_discrete_sequence=color_scheme
            )
        elif chart_type == "Donut Chart":
            donut_data = sales_by_day.melt(id_vars=['month', 'categoryName'], value_vars=sales_by_day.columns[2:], 
                                            var_name='day', value_name='total_selling_price')
            fig = px.pie(
                donut_data,
                names='day',
                values='total_selling_price',
                title="Sales Distribution by Day",
                hole=0.4,
                color_discrete_sequence=color_scheme
            )
            fig.update_layout(height=600)

        st.plotly_chart(fig, use_container_width=True)

        # Modify the last line chart for "Weekly Sales Trend by Category"
        sales_by_week_trend = sales_by_week.melt(id_vars=['month', 'categoryName'], value_vars=sales_by_week.columns[2:], 
                                                var_name='week_label', value_name='total_selling_price')

        # Aggregate the total sales per week (across categories)
        sales_by_week_trend_agg = sales_by_week_trend.groupby(['week_label', 'categoryName'], as_index=False)['total_selling_price'].sum()

        fig_week_trend = px.line(
            sales_by_week_trend_agg,
            x='week_label',
            y='total_selling_price',
            color='categoryName',
            title="Weekly Sales Trend by Category",
            labels={'total_selling_price': 'Sales'},
            color_discrete_sequence=color_scheme
        )

        st.plotly_chart(fig_week_trend, use_container_width=True)
    else:
        print("Select Categories for chart")
