import streamlit as st
import pandas as pd
import plotly.express as px

# Load the GPS coordinates from the CSV file
def load_coordinates(file_path="gps_co_ordinates/co_ordinates.csv"):
    gps_df = pd.read_csv(file_path)
    return gps_df[['storeName', 'latitude', 'longitude']]

# Function to display store performance analysis
def store_performance_analysis(data, date_filtered_data, selected_brands, selected_stores):
    st.markdown("<h1 style='text-align: center; color: green;'>Stores Performance</h1>", unsafe_allow_html=True)

    # Calculate total sales for the entire date-filtered data
    total_store_sales = (date_filtered_data['sellingPrice'] * date_filtered_data['quantity']).sum()

    # Calculate sales for all brands by store (using date_filtered_data)
    all_brands_store_sales = date_filtered_data.groupby('storeName').agg(
        total_store_sales=('sellingPrice', lambda x: (x * date_filtered_data.loc[x.index, 'quantity']).sum())
    ).reset_index()

    # Filter data for selected brands
    filtered_data = data[data['brandName'].isin(selected_brands)]
    filtered_data['total_selling_price'] = filtered_data['sellingPrice'] * filtered_data['quantity']
    filtered_data['total_cost_price'] = filtered_data['costPrice'] * filtered_data['quantity']
    filtered_data['profit'] = filtered_data['total_selling_price'] - filtered_data['total_cost_price']

    date_filtered_data['total_selling_price'] = date_filtered_data['sellingPrice'] * date_filtered_data['quantity']
    date_filtered_data['total_cost_price'] = date_filtered_data['costPrice'] * date_filtered_data['quantity']
    date_filtered_data['profit'] = date_filtered_data['total_selling_price'] - date_filtered_data['total_cost_price']

    # Filter data for selected stores
    filtered_data = filtered_data[filtered_data['storeName'].isin(selected_stores)]

    # Aggregate data by storeName for filtered data
    store_performance = filtered_data.groupby('storeName').agg(
        total_selling_price=('total_selling_price', 'sum'),
        total_quantity=('quantity', 'sum'),
        profit=('profit', 'sum'),
    ).reset_index()

    # Sort the DataFrame by total_selling_price in descending order
    store_performance = store_performance.sort_values(by='total_selling_price', ascending=False)

    # Merge with all_brands_store_sales to get total store sales
    store_performance = store_performance.merge(all_brands_store_sales, on='storeName', how='left')

    # Add a column for total store sales for the entire date range
    store_performance['total_store_sales'] = total_store_sales

    # Ensure the relevant columns are numeric
    store_performance['total_selling_price'] = pd.to_numeric(store_performance['total_selling_price'], errors='coerce')
    store_performance['total_store_sales'] = pd.to_numeric(store_performance['total_store_sales'], errors='coerce')

    # Calculate the contribution percentage of total_selling_price to total_store_sales
    store_performance['contribution_percentage'] = (
        (store_performance['total_selling_price'] / store_performance['total_store_sales']) * 100
    )
    store_performance['contribution_percentage'] = store_performance['contribution_percentage'].apply(lambda x: f"{x:.2f}%")

    # Format profit contribution for better readability
    overall_profit = date_filtered_data['profit'].sum()
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
            y='total_selling_price', 
            title="Top Stores by Total Selling Price",
            labels={'total_selling_price': 'Total Selling Price'},
            color='storeName',  
            color_discrete_sequence=color_palette  
        )
        if show_data_labels:
            fig.update_traces(text=store_performance['total_selling_price'], textposition="outside")
    elif chart_type == "Pie Chart":
        fig = px.pie(
            store_performance, 
            names='storeName', 
            values='total_selling_price', 
            title="Top Stores by Total Selling Price",
            color='storeName',  
            color_discrete_sequence=color_palette  
        )
        if show_data_labels:
            fig.update_traces(textinfo='label+value', textposition="inside")
    elif chart_type == "Line Chart":
        fig = px.line(
            store_performance, 
            x='storeName', 
            y='total_selling_price', 
            title="Top Stores by Total Selling Price",
            labels={'total_selling_price': 'Total Selling Price'},
            color='storeName',  
            markers=True,
            color_discrete_sequence=color_palette
        )
        if show_data_labels:
            fig.update_traces(text=store_performance['total_selling_price'], textposition="top center")

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<h4 style='text-align: center; color: green;'>Store performance dataframe</h4>", unsafe_allow_html=True)

    # Format columns for display
    store_performance['total_selling_price'] = store_performance['total_selling_price'].apply(lambda x: f"{x:.2f}")
    store_performance['profit'] = store_performance['profit'].apply(lambda x: f"{x:.2f}")
    store_performance['total_store_sales'] = store_performance['total_store_sales'].apply(lambda x: f"{x:.2f}")

    st.dataframe(store_performance)

    # Load GPS coordinates for stores from CSV file
    gps_df = load_coordinates()
    
    # Merge preloaded GPS coordinates with store_performance
    store_performance = store_performance.merge(gps_df, on='storeName', how='left')

    # Filter out stores without valid latitude and longitude
    store_performance = store_performance.dropna(subset=['latitude', 'longitude'])

    st.markdown("<h3 style='text-align: center; color: blue;'>Store Location Map</h3>", unsafe_allow_html=True)

    fig_map = px.scatter_mapbox(
        store_performance,
        lat='latitude',
        lon='longitude',
        size=store_performance['total_selling_price'].astype(float),
        size_max=50,
        color='storeName',
        hover_name='storeName', 
        hover_data={'storeName': True, 'total_selling_price': True},
        title="Store Locations",
        zoom=5,
    )
    fig_map.update_layout(mapbox_style="open-street-map", height=800)
    st.plotly_chart(fig_map, use_container_width=True)
