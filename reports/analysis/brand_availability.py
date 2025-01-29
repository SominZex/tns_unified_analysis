import pandas as pd
import streamlit as st
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

def top_n_brand_availability_analysis(store_data_filtered):
    # ---- Top N Brand Availability Analysis ----
    st.markdown("<h2 style='color: green; text-align: center;'>AVAILABILITY OF TOP-N BRANDS</h2>", unsafe_allow_html=True)

    # Get unique brand names for selection
    unique_brands = store_data_filtered['brandName'].unique()

    # Ensure there are brands to analyze
    if len(unique_brands) == 0:
        st.warning("No brands available for analysis.")
        return

    # Unique key for the slider
    n_brands = st.slider(
        "Select the number of top brands to analyze:",
        min_value=1,
        max_value=len(unique_brands),
        value=20,
        key="n_brands_slider" 
    )

    # Group by brandName and calculate the availability
    brand_availability = store_data_filtered.groupby('brandName').agg(
        total_availability=('quantity', 'sum'), 
        total_products=('productId', 'count')
    ).reset_index()

    # Sort brands by total availability and select top N
    top_n_brands_availability = brand_availability.nlargest(n_brands, 'total_availability')

    # User input for color selection for brand availability plots
    selected_brand_color = st.selectbox(
        "Select Color Scale for Availability Plot:",
        ['Blues', 'Reds', 'Greens', 'Purples', 'Oranges'],
        key="availability_color_scale"
    )

    # User input to toggle data labels for Top N Brand Availability Analysis
    show_data_labels_availability = st.checkbox(
        "Show Data Labels for Top N Brand Availability Analysis",
        value=True,
        key="show_data_labels_availability"
    )

    # User input for chart type selection
    chart_type = st.selectbox(
        "Select Chart Type for Availability:",
        ["Bar Chart", "Donut Chart", "Line Chart"],
        key="availability_chart_type_selection"
    )

    # Create plots based on selected chart type
    if chart_type == "Bar Chart":
        create_bar_chart(top_n_brands_availability, selected_brand_color, show_data_labels_availability, n_brands)

    elif chart_type == "Donut Chart":
        create_donut_chart(top_n_brands_availability, selected_brand_color, show_data_labels_availability, n_brands)

    elif chart_type == "Line Chart":
        create_line_chart(top_n_brands_availability, selected_brand_color, show_data_labels_availability, n_brands)

    # Display the DataFrame for Top N Brands including availability
    st.dataframe(top_n_brands_availability)

def create_bar_chart(top_n_brands_availability, color_palette, show_labels, n_brands):
    """Create a Bar Chart for Top N Brand Availability."""
    # Create Plotly Bar Chart
    fig_brand_availability_bar = px.bar(
        top_n_brands_availability,
        x='brandName',
        y='total_availability',
        title=f'Top {n_brands} Brands by Total Availability',
        labels={'total_availability': 'Total Available Products', 'brandName': 'Brand'},
        color='total_availability', 
        color_continuous_scale=color_palette 
    )
    if show_labels:
        fig_brand_availability_bar.update_traces(texttemplate='%{y:.2f}', textposition='outside')

    # Adjusting the figure layout for size (1100x600)
    fig_brand_availability_bar.update_layout(height=600, width=1100)

    st.plotly_chart(fig_brand_availability_bar, use_container_width=False)

def create_donut_chart(top_n_brands_availability, color_palette, show_labels, n_brands):
    """Create a Donut Chart for Top N Brand Availability."""
    # Create Plotly Donut Chart
    fig_brand_availability_donut = px.pie(
        top_n_brands_availability,
        names='brandName',
        values='total_availability',
        title=f'Top {n_brands} Brands by Total Availability (Donut Chart)',
        hole=0.4 
    )
    if show_labels:
        fig_brand_availability_donut.update_traces(textinfo='percent+label')

    # Adjusting the figure layout for size (1100x600)
    fig_brand_availability_donut.update_layout(height=600, width=1100)

    st.plotly_chart(fig_brand_availability_donut, use_container_width=False)

def create_line_chart(top_n_brands_availability, color_palette, show_labels, n_brands):
    """Create a Line Chart for Top N Brand Availability."""
    # Create Plotly Line Chart
    fig_brand_availability_line = px.line(
        top_n_brands_availability,
        x='brandName',
        y='total_availability',
        title=f'Top {n_brands} Brands by Total Availability (Line Chart)',
        labels={'total_availability': 'Total Available Products', 'brandName': 'Brand'},
        line_shape='linear'
    )
    if show_labels:
        fig_brand_availability_line.add_scatter(
            x=top_n_brands_availability['brandName'],
            y=top_n_brands_availability['total_availability'],
            mode='text',
            text=top_n_brands_availability['total_availability'].round(2),
            textposition='top center'
        )

    # Adjusting the figure layout for size (1100x600)
    fig_brand_availability_line.update_layout(height=600, width=1100)

    st.plotly_chart(fig_brand_availability_line, use_container_width=False)
