import pandas as pd
import streamlit as st
import plotly.express as px

def top_n_product_availability_analysis(store_data):
    st.title("Top N Product Availability Analysis")

    # Select a store from the store names
    store_names = store_data['storeName'].unique()
    selected_store = st.selectbox("Select a Store:", store_names, key="store_selector_availability")

    # Filter the data for the selected store
    store_data_filtered = store_data[store_data['storeName'] == selected_store]

    # Group availability by product for the selected store
    product_availability = store_data_filtered.groupby('productName').agg(
        total_quantity=('quantity', 'sum'),
    ).reset_index()

    # Sort products by total quantity and get the top N products
    unique_products = product_availability['productName'].unique()
    n_products = st.slider("Select the number of top products to analyze:", 
                            min_value=1, 
                            max_value=len(unique_products), 
                            value=50, 
                            key="n_products_slider")

    top_n_products_availability = product_availability.nlargest(n_products, 'total_quantity')

    # User input for plot type for Top N Product Availability Analysis
    plot_type = st.selectbox("Select Plot Type for Top N Product Availability Analysis:", 
                              ["Bar Chart", "Donut Chart", "Line Chart"], 
                              key="plot_type_availability")

    # User input for color selection for product availability plots
    color_options_availability = px.colors.named_colorscales()
    selected_color_availability = st.selectbox("Select Color Scale for Top N Product Availability Plot:", 
                                                 color_options_availability, 
                                                 key="color_scale_availability")

    # User input to toggle data labels for Top N Product Availability Analysis
    show_data_labels_availability = st.checkbox("Show Data Labels for Top N Product Availability Analysis", 
                                                 value=True, 
                                                 key="show_data_labels_availability_checkbox")

    chart_width, chart_height = 1000, 600

    # Create the plot based on the selected type for Top N Product Availability Analysis
    if plot_type == "Bar Chart":
        fig_availability = px.bar(
            top_n_products_availability,
            x='productName',
            y='total_quantity',
            title='Top N Products by Total Quantity Available',
            labels={'total_quantity': 'Total Quantity', 'productName': 'Product Name'},
            color='total_quantity', 
            color_continuous_scale=selected_color_availability 
        )
        if show_data_labels_availability:
            fig_availability.update_traces(texttemplate='%{y:.2f}', textposition='outside')

        # Update layout with fixed width and height
        fig_availability.update_layout(width=chart_width, height=chart_height)

    elif plot_type == "Donut Chart":
        fig_availability = px.pie(
            top_n_products_availability,
            names='productName',
            values='total_quantity',
            title='Top N Products by Total Quantity Available (Donut Chart)',
            hole=0.4
        )
        if show_data_labels_availability:
            fig_availability.update_traces(textinfo='percent+label')

        # Update layout with fixed width and height
        fig_availability.update_layout(width=chart_width, height=chart_height)

    elif plot_type == "Line Chart":
        fig_availability = px.line(
            top_n_products_availability,
            x='productName',
            y='total_quantity',
            title='Top N Products by Total Quantity Available (Line Chart)',
            labels={'total_quantity': 'Total Quantity', 'productName': 'Product Name'},
            line_shape='linear'
        )
        if show_data_labels_availability:
            fig_availability.add_scatter(
                x=top_n_products_availability['productName'],
                y=top_n_products_availability['total_quantity'],
                mode='text',
                text=top_n_products_availability['total_quantity'].round(2),
                textposition='top center'
            )

        # Update layout with fixed width and height
        fig_availability.update_layout(width=chart_width, height=chart_height)

    # Display the plot and DataFrame for Top N Product Availability Analysis
    st.plotly_chart(fig_availability, use_container_width=False)
    st.dataframe(top_n_products_availability)
