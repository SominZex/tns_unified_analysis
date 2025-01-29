import pandas as pd
import streamlit as st

def format_currency(value):
    """Format the value as currency in Rupees with commas."""
    return f"₹{value:,.2f}"

def calculate_profits(data, selected_store, start_date, end_date):
    st.markdown("<h4 style='color: green; text-align: center;'>Profit KPI</h4>", unsafe_allow_html=True)

    # Filter data for the selected date range and store
    filtered_data = data[(data['orderDate'] >= start_date) & (data['orderDate'] <= end_date)]
    
    # Calculate profit per store for the filtered data
    store_profit = filtered_data.groupby('storeName').apply(
        lambda x: (x['totalProductPrice'] - (x['costPrice']* x['quantity'])).sum()
    ).reset_index()
    store_profit.columns = ['storeName', 'profit']

    # Calculate overall profit for the filtered data
    overall_profit = store_profit['profit'].sum()

    # Calculate date range in days
    date_range_days = (end_date - start_date).days + 1

    # Calculate overall average profit using the new formula
    overall_average_profit = 42358 * date_range_days * 0.3

    # Ensure the selected store exists in the filtered data
    if selected_store in store_profit['storeName'].values:
        # Calculate store-specific profit
        store_profit_value = store_profit.loc[store_profit['storeName'] == selected_store, 'profit'].values[0]

        # Calculate store average profit
        store_average_profit = store_profit_value / date_range_days if date_range_days > 0 else 0
    else:
        # Handle cases where the store has no data in the selected range
        store_profit_value = 0
        store_average_profit = 0

    # Calculate store revenue for the selected store
    store_revenue = filtered_data[filtered_data['storeName'] == selected_store]['totalProductPrice'].sum()

    # Calculate profit contribution percentage
    profit_contribution_percentage = (store_profit_value / store_revenue * 100) if store_revenue > 0 else 0

    # Prepare the results as a dictionary
    results = {
        'selected_store_profit': store_profit_value,
        'overall_average_profit': overall_average_profit,
        'selected_store_average_profit': store_average_profit,
        'profit_contribution_percentage': profit_contribution_percentage
    }

    return results

def display_profit_metrics(data, selected_store, start_date, end_date):
    # Calculate profits
    profits = calculate_profits(data, selected_store, start_date, end_date)

    # Create three equal columns
    col1, col2, col3 = st.columns(3, gap="large")

    # Custom CSS for perfect alignment and conditional formatting
    custom_metric_style = """
           <style>
            [data-testid="metric-container"] {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                margin: 0 auto;
                padding: 0;
            }
            [data-testid="stMetricValue"] {
                display: flex;
                justify-content: center;
                align-items: center;
            }
            [data-testid="stMetricLabel"] {
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .negative {
                color: rgb(255, 43, 43) !important;
            }
            .positive {
                color: rgb(9, 171, 59) !important;
            }
        </style>
    """
    st.markdown(custom_metric_style, unsafe_allow_html=True)

    # Store Profit in col1
    with col1:
        st.metric(
            "Store Profit",
            format_currency(profits['selected_store_profit'])
        )

    # Overall Average Profit in col2
    with col2:
        st.metric(
            "Overall Average Profit",
            format_currency(profits['overall_average_profit'])
        )

    # Profit Contribution Percentage in col3 with conditional formatting
    with col3:
        profit_percentage = profits['profit_contribution_percentage']
        st.metric(
            "Profit to Revenue Percentage",
            f"{profit_percentage:.2f}%"
        )
    
    # Return the profits dictionary
    return profits
