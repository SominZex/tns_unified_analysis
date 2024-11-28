import streamlit as st
import plotly.express as px

def category_breakdown_analysis(data, selected_stores):
    st.markdown("<h1 style='text-align: center; color: green;'>Category Breakdown</h1>", unsafe_allow_html=True)
    
    # Strip extra spaces from categoryName and storeName to ensure consistency
    data['categoryName'] = data['categoryName'].str.strip()
    data['storeName'] = data['storeName'].str.strip()

    # Filter data for selected stores
    filtered_data = data[data['storeName'].isin(selected_stores)]

    # Check if filtered data is empty
    if filtered_data.empty:
        st.warning("No data found for the selected stores.")
        return

    # Calculate sales and cost by category and store
    filtered_data['total_sales'] = filtered_data['sellingPrice'] * filtered_data['quantity']
    filtered_data['total_cost'] = filtered_data['costPrice'] * filtered_data['quantity']

    # Sidebar options for filtering categories
    st.sidebar.subheader("Category Filters")

    # Get a list of unique categories available in the filtered data
    available_categories = filtered_data['categoryName'].unique().tolist()

    # Allow the user to select specific categories for comparison (empty by default)
    selected_categories = st.multiselect(
        "Select Categories to Compare", options=available_categories, default=[]
    )

    # If no category is selected for comparison, select all available categories
    if not selected_categories:
        selected_categories = available_categories

    # Filter data by selected categories for comparison
    filtered_data_for_comparison = filtered_data[filtered_data['categoryName'].isin(selected_categories)]

    # Aggregate total_sales, total_cost, and quantity by storeName
    store_sales = filtered_data_for_comparison.groupby('storeName').agg(
        total_sales=('total_sales', 'sum'),
        total_cost=('total_cost', 'sum'),
        total_quantity=('quantity', 'sum')
    ).reset_index()

    # Calculate profit and profit margin
    store_sales['profit'] = store_sales['total_sales'] - store_sales['total_cost']

    # Display data table for store sales breakdown
    st.dataframe(store_sales)

    # Sidebar options for chart customization
    st.sidebar.subheader("Chart Settings")
    
    chart_type = st.sidebar.selectbox(
        "Select Chart Type", 
        ["Bar Chart", "Pie Chart", "Treemap"], 
        key="category_breakdown_chart_type"
    )
    
    show_data_labels = st.sidebar.checkbox(
        "Show Data Labels", 
        False, 
        key="category_breakdown_show_data_labels"
    )

    # Define a color palette for the charts
    color_palette = px.colors.qualitative.Set3
    
    # Chart rendering based on user selection
    if chart_type == "Bar Chart":
        fig = px.bar(filtered_data_for_comparison, x='categoryName', y='total_sales', color='storeName', 
                     title="Category Breakdown by Sales", labels={'total_sales': 'Sales'}, 
                     color_discrete_sequence=color_palette, barmode="group")
        if show_data_labels:
            fig.update_traces(text=filtered_data_for_comparison['total_sales'], textposition="outside")
    elif chart_type == "Pie Chart":
        fig = px.pie(filtered_data_for_comparison, names='categoryName', values='total_sales', 
                     title="Category Breakdown by Sales", color='categoryName', 
                     color_discrete_sequence=color_palette)
        if show_data_labels:
            fig.update_traces(textinfo="label+percent")
    elif chart_type == "Treemap":
        fig = px.treemap(filtered_data_for_comparison, path=['storeName', 'categoryName'], values='total_sales', 
                         title="Category Breakdown by Sales", color='categoryName', 
                         color_discrete_sequence=color_palette)

    st.plotly_chart(fig, use_container_width=True)
