import pandas as pd
import streamlit as st
import plotly.express as px

def order_analysis(store_data):
    st.markdown("<h4 style='color: green; text-align: center;'>Order Analysis</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # Clean the customerNumber column to determine valid entries
    valid_customers = store_data['customerNumber'].apply(lambda x: str(x).isdigit())
    store_data['valid_customer'] = valid_customers
    total_customers = valid_customers.sum()
    total_entries = len(store_data)
    customer_collection_percentage = (total_customers / total_entries) * 100 if total_entries > 0 else 0

    # Calculate total orders, total quantity sold, and total revenue
    total_orders_count = len(store_data['invoice'])
    total_quantity = store_data['quantity'].sum()
    total_revenue = store_data['totalProductPrice'].sum()
    total_cost = store_data['costPrice'].sum()
    total_profit = total_revenue - total_cost

    # Display metrics
    col1, col2, col3 , col4 = st.columns(4)
    col1.metric("Total Unique Orders", total_orders_count)
    col2.metric("Total Quantity", total_quantity)
    col3.metric("Customer Info Collected", f"{customer_collection_percentage:.2f}%")
    col4.metric('Total Numbers Collected', total_customers)

    # Check if a date column exists or if it's named differently
    date_column = None
    for col in store_data.columns:
        if 'date' in col.lower():
            date_column = col
            break

    if date_column:
        # Convert date column to datetime if it's not already
        store_data[date_column] = pd.to_datetime(store_data[date_column])

        # Aggregate data for plotting the number of valid customers collected
        daily_metrics = store_data.groupby(date_column).agg(
            valid_customers=('valid_customer', 'sum'),
            total_entries=('valid_customer', 'count')
        ).reset_index()

        # Create the bar chart for the number of valid customers collected
        fig = px.bar(
            daily_metrics,
            x=date_column,
            y='valid_customers',
            title='Number of Valid Customers Collected Over Time',
            labels={date_column: 'Date', 'valid_customers': 'Valid Customers Collected'},
            text='valid_customers' 
        )
        
        fig.update_traces(textposition='outside')  
        fig.update_layout(width=1100, height=400)
        st.plotly_chart(fig)
    else:
        st.warning("No date column found in the dataset. Cannot plot valid customers over time.")

    # Prepare data for download
    store_data['totalProductPrice'] = store_data['totalProductPrice'].apply(lambda x: f"{x:.2f}")
    store_data['costPrice'] = store_data['costPrice'].apply(lambda x: f"{x:.2f}")

    @st.cache_data
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv_orders = convert_df(store_data)

    st.sidebar.download_button(
        label="Download Order Data",
        data=csv_orders,
        file_name='filtered_orders.csv',
        mime='text/csv',
    )
