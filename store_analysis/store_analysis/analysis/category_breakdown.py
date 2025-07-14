import streamlit as st
import plotly.express as px
import pandas as pd

# Cache data preprocessing
@st.cache_data
def preprocess_data(data):
    data['categoryName'] = data['categoryName'].str.strip()
    data['storeName'] = data['storeName'].str.strip()
    # Calculate total_sales and total_cost if not already present
    if 'total_sales' not in data.columns:
        data['total_sales'] = data['sellingPrice'] * data['quantity']
    if 'total_cost' not in data.columns:
        data['total_cost'] = data['costPrice'] * data['quantity']
    return data

# Cache filtered and aggregated data
@st.cache_data
def filter_and_aggregate(data, selected_stores, selected_categories):
    # Filter data for selected stores and categories
    filtered_data = data[
        (data['storeName'].isin(selected_stores)) &
        (data['categoryName'].isin(selected_categories))
    ]
    if filtered_data.empty:
        return None, None
    # Aggregate data for visualization
    store_sales = filtered_data.groupby('storeName').agg(
        total_sales=('total_sales', 'sum'),
        total_cost=('total_cost', 'sum'),
        total_quantity=('quantity', 'sum')
    ).reset_index()
    store_sales['profit'] = store_sales['total_sales'] - store_sales['total_cost']
    return filtered_data, store_sales

def category_breakdown_analysis(data, selected_stores):
    st.markdown("<h1 style='text-align: center; color: green;'>Category Breakdown</h1>", unsafe_allow_html=True)

    # Preprocess data
    data = preprocess_data(data)

    # Filter by selected stores
    filtered_data = data[data['storeName'].isin(selected_stores)]
    if filtered_data.empty:
        st.warning("No data found for the selected stores.")
        return

    # Sidebar filters
    st.sidebar.subheader("Category Filters")
    # Limit categories to top 20 by frequency
    available_categories = filtered_data['categoryName'].value_counts().nlargest(20).index.tolist()

    # Multi-select for selecting multiple categories from the top 20 (no default selection)
    selected_categories = st.sidebar.multiselect(
        "Select Categories to Compare", 
        options=available_categories, 
        default=[] 
    )

    if not selected_categories:
        st.warning("No categories selected from the sidebar.")
        return

    # Aggregate data for the selected categories
    filtered_data_for_comparison, store_sales = filter_and_aggregate(
        filtered_data, selected_stores, selected_categories
    )
    if filtered_data_for_comparison is None or store_sales is None:
        st.warning("No data available after filtering.")
        return

    # Display aggregated data
    st.dataframe(store_sales)

    # Sidebar settings for charts
    st.sidebar.subheader("Chart Settings")
    chart_type = st.sidebar.selectbox(
        "Select Chart Type",
        ["Bar Chart", "Pie Chart"], 
        key="category_breakdown_chart_type"
    )
    show_data_labels = st.sidebar.checkbox(
        "Show Data Labels",
        False,
        key="category_breakdown_show_data_labels"
    )
    color_palette = px.colors.qualitative.Set3

    # Generate charts
    if chart_type == "Bar Chart":
        fig = px.bar(
            filtered_data_for_comparison,
            x='categoryName',
            y='total_sales',
            color='storeName',
            title="Category Breakdown by Sales",
            labels={'total_sales': 'Sales'},
            color_discrete_sequence=color_palette,
            barmode="group"
        )
        if show_data_labels:
            fig.update_traces(texttemplate='%{y:.2f}', textposition="outside")
    elif chart_type == "Pie Chart":
        fig = px.pie(
            filtered_data_for_comparison,
            names='categoryName',
            values='total_sales',
            title="Category Breakdown by Sales",
            color_discrete_sequence=color_palette
        )
        if show_data_labels:
            fig.update_traces(textinfo="label+percent")

    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
