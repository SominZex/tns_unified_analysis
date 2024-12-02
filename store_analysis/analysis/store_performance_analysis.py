import streamlit as st
import pandas as pd
import plotly.express as px

# Load the GPS coordinates from the CSV file
def load_coordinates(file_path="store_analysis/gps_co_ordinates/co_ordinates.csv"):
    gps_df = pd.read_csv(file_path)
    return gps_df[['storeName', 'latitude', 'longitude']]

# Function to display store performance analysis
def store_performance_analysis(data, date_filtered_data, selected_stores):
    st.markdown("<h1 style='text-align: center; color: green;'>Stores Performance</h1>", unsafe_allow_html=True)

    # Filter data for selected stores
    filtered_data = data[data['storeName'].isin(selected_stores)]
    filtered_data['total_store_sales'] = filtered_data['sellingPrice'] * filtered_data['quantity']
    filtered_data['total_cost_price'] = filtered_data['costPrice'] * filtered_data['quantity']
    filtered_data['profit'] = filtered_data['total_store_sales'] - filtered_data['total_cost_price']

    # Aggregate data by storeName
    store_performance = filtered_data.groupby('storeName').agg(
        total_store_sales=('total_store_sales', 'sum'),
        total_quantity=('quantity', 'sum'),
        profit=('profit', 'sum'),
    ).reset_index()

    # Sort by total_store_sales in descending order
    store_performance = store_performance.sort_values(by='total_store_sales', ascending=False)

    # Format profit contribution for better readability
    overall_profit = store_performance['profit'].sum()
    store_performance['profit_contribution'] = (store_performance['profit'] / overall_profit) * 100
    store_performance['profit_contribution'] = store_performance['profit_contribution'].apply(lambda x: f"{x:.2f}%")

    # Sidebar options for chart customization
    st.sidebar.subheader("Store Performance Chart Settings")
    chart_type = st.sidebar.selectbox("Select Chart Type", ["Bar Chart", "Pie Chart", "Line Chart"])
    show_data_labels = st.sidebar.checkbox("Show Data Labels", False, key="store_performance_show_data_labels")

    # Define a color palette for the charts
    color_palette = px.colors.qualitative.Plotly

    # Chart rendering based on user selection
    if chart_type == "Bar Chart":
        fig = px.bar(
            store_performance,
            x='storeName',
            y='total_store_sales',
            title="Top Stores by Total Store Sales",
            labels={'total_store_sales': 'Total Store Sales'},
            color='storeName',
            color_discrete_sequence=color_palette
        )
        if show_data_labels:
            fig.update_traces(text=store_performance['total_store_sales'], textposition="outside")
    elif chart_type == "Pie Chart":
        fig = px.pie(
            store_performance,
            names='storeName',
            values='total_store_sales',
            title="Top Stores by Total Store Sales",
            color='storeName',
            color_discrete_sequence=color_palette
        )
        if show_data_labels:
            fig.update_traces(textinfo='label+value', textposition="inside")
    elif chart_type == "Line Chart":
        fig = px.line(
            store_performance,
            x='storeName',
            y='total_store_sales',
            title="Top Stores by Total Store Sales",
            labels={'total_store_sales': 'Total Store Sales'},
            color='storeName',
            markers=True,
            color_discrete_sequence=color_palette
        )
        if show_data_labels:
            fig.update_traces(text=store_performance['total_store_sales'], textposition="top center")

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<h4 style='text-align: center; color: green;'>Store performance dataframe</h4>", unsafe_allow_html=True)

    # Round numeric columns and format them for better readability
    store_performance['total_store_sales'] = store_performance['total_store_sales'].round(2).apply(lambda x: f"{x:.2f}")
    store_performance['profit'] = store_performance['profit'].round(2).apply(lambda x: f"{x:.2f}")

    # Display data table
    st.dataframe(store_performance)

    # Load GPS coordinates for stores from CSV file
    gps_df = load_coordinates()
    
    # Merge GPS coordinates with store_performance
    store_performance = store_performance.merge(gps_df, on='storeName', how='left')

    # Filter out stores without valid latitude and longitude
    store_performance = store_performance.dropna(subset=['latitude', 'longitude'])

    # Map visualization
    st.markdown("<h3 style='text-align: center; color: blue;'>Store Location Map</h3>", unsafe_allow_html=True)

    # Ensure that total_store_sales is numeric before calculating size
    store_performance['total_store_sales'] = pd.to_numeric(store_performance['total_store_sales'], errors='coerce')
    size_variable = store_performance['total_store_sales'].fillna(0)

    fig_map = px.scatter_mapbox(
        store_performance,
        lat='latitude',
        lon='longitude',
        size=size_variable,
        size_max=50,
        color='storeName',
        hover_name='storeName',
        hover_data={'storeName': True, 'total_store_sales': True},
        title="Store Locations",
        zoom=5,
    )

    fig_map.update_layout(
        mapbox_style="open-street-map",
        height=800,
    )

    st.plotly_chart(fig_map, use_container_width=True)
