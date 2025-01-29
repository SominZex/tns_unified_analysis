
# New KPI metrics section
import streamlit as st
"""

st.markdown("<h2 style='color: green; text-align: center;'>Additional Store Performance Metrics</h2>", unsafe_allow_html=True)

# Function to calculate new metrics
def calculate_additional_metrics(store_data_filtered):
    average_sales_selected = store_data_filtered['totalProductPrice'].mean()
    total_revenue_selected = store_data_filtered['totalProductPrice'].sum()
    
    overall_average_dynamic = data['totalProductPrice'].mean()
    overall_total_revenue_dynamic = data['totalProductPrice'].sum()
    
    selected_store_percentage_contribution_dynamic = (total_revenue_selected / overall_total_revenue_dynamic) * 100 if overall_total_revenue_dynamic > 0 else 0
    percentage_difference_dynamic = ((average_sales_selected - overall_average_dynamic) / overall_average_dynamic) * 100 if overall_average_dynamic > 0 else 0

    return average_sales_selected, total_revenue_selected, selected_store_percentage_contribution_dynamic, overall_average_dynamic, percentage_difference_dynamic

# Get additional metrics
average_sales_selected, total_revenue_selected, selected_store_percentage_contribution_dynamic, overall_average_dynamic, percentage_difference_dynamic = calculate_additional_metrics(store_data_filtered)

# Display additional metrics function
def display_additional_metric(column, label, value, percentage_difference):
    column.metric(label, value)
    if percentage_difference > 0:
        delta_text = f'<span style="color: green;">+{percentage_difference:.2f}%</span>'
    elif percentage_difference < 0:
        delta_text = f'<span style="color: red;">{percentage_difference:.2f}%</span>'
    else:
        delta_text = f'<span style="color: grey;">{percentage_difference:.2f}%</span>'
    column.markdown(delta_text, unsafe_allow_html=True)

# Display additional KPIs as cards
col5, col6, col7, col8, col9 = st.columns(5)

# Store Average Sales (Dynamic)
display_additional_metric(col5, "Avg Sales (Dynamic)", f"₹{average_sales_selected:,.2f}", percentage_difference_dynamic)

# Total Revenue (Dynamic)
col6.metric("Total Revenue (Dynamic)", f"₹{total_revenue_selected:,.2f}")

# Percentage Contribution to Total Revenue (Dynamic)
col7.metric("% Contribution to Total Revenue (Dynamic)", f"{selected_store_percentage_contribution_dynamic:.2f}%", delta_color="normal")

# Company Average Sales (Dynamic)
col8.metric("Company Average Sales (Dynamic)", f"₹{overall_average_dynamic:,.2f}")

# Difference Between Company and Selected Store Average Sales (Dynamic)
col9.metric("Difference (Dynamic)", f"{percentage_difference_dynamic:.2f}%", delta_color="normal") """


