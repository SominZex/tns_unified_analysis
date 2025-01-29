import pandas as pd
import streamlit as st
import plotly.express as px

def low_performing_brand_analysis(store_data):
    st.markdown("<h4 style='color: green; text-align: center;'>Revenue VS Low performing Brands</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # Group the data by brandName to calculate product count, total sales, total cost, profit, and profit margin
    low_performing_brands = store_data.groupby('brandName').agg(
        product_count=('productId', 'nunique'),
        quantity_sold=('quantity', 'sum'),
        total_revenue=('totalProductPrice', 'sum'), 
        total_cost=('costPrice', 'sum') 
    ).reset_index()

    # Calculate profit and profit margin
    low_performing_brands['profit'] = low_performing_brands['total_revenue'] - low_performing_brands['total_cost']
    low_performing_brands['profit_margin'] = (low_performing_brands['profit'] / low_performing_brands['total_revenue']) * 100

    # Format profit margin as a percentage with the '%' symbol
    low_performing_brands['profit_margin'] = low_performing_brands['profit_margin'].map(lambda x: f"{x:.2f}%")

    # Sort the brands by quantity sold in ascending order for analysis
    low_performing_brands = low_performing_brands.sort_values(by='quantity_sold')

    # Check if there are any brands in the analysis
    if not low_performing_brands.empty:
        # Move the controls to the sidebar
        st.sidebar.markdown("## Filter Options for low performing brands")
        
        color_scale_low = st.sidebar.selectbox("Select Color Scale for Low sale brands:", 
                                           options=['Viridis', 'Cividis', 'Plasma', 'Blues'], 
                                           index=2, key = "low_performing_color_brands")

        # Choose plot type
        plot_type_low = st.sidebar.selectbox("Select Plot Type for low sales brands:", 
                                         options=['Bar Plot', 'Line Plot'], 
                                         index=0, key = "low_performing_brands_plot")

        low_performing_brands_sorted_by_revenue = low_performing_brands.sort_values(by='total_revenue')

        # Plot Total Revenue
        if plot_type_low == 'Bar Plot':
            fig_total_revenue = px.bar(
                low_performing_brands_sorted_by_revenue,
                x='brandName',
                y='total_revenue',
                title='Total Revenue by Low Performing Brands',
                labels={'total_revenue': 'Total Revenue', 'brandName': 'Brand'},
                color='total_revenue',
                color_continuous_scale=color_scale_low
            )
        else: 
            fig_total_revenue = px.line(
                low_performing_brands_sorted_by_revenue,
                x='brandName',
                y='total_revenue',
                title='Total Revenue by Low Performing Brands',
                labels={'total_revenue': 'Total Revenue', 'brandName': 'Brand'},
                markers=True
            )

        # Set the size of the Total Revenue plot
        fig_total_revenue.update_layout(width=1100, height=400)
        # Display the Total Revenue plot
        st.plotly_chart(fig_total_revenue)
        
    else:
        st.warning("No low performing brands found in the selected store.")


    low_performing_brands['total_revenue'] = low_performing_brands['total_revenue'].apply(lambda x: f"{x:.2f}")
    low_performing_brands['total_cost'] = low_performing_brands['total_cost'].apply(lambda x: f"{x:.2f}")

    @st.cache_data
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv_brands = convert_df(low_performing_brands)

    st.sidebar.download_button(
            label="Download low performing brands Data",
            data=csv_brands,   
            file_name='low_performing_brands.csv',
            mime='text/csv',
        )