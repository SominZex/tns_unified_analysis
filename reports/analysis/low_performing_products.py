import pandas as pd
import streamlit as st
import plotly.express as px

def low_performing_product_analysis(store_data):
    st.markdown("<h4 style='color: green; text-align: center;'>LOW PERFORMING PRODUCTS</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # Group the data by productId to calculate sales metrics
    low_performing_products = store_data.groupby('productId').agg(
        product_name=('productName', 'first'),
        quantity_sold=('quantity', 'sum'),
        total_revenue=('totalProductPrice', 'sum'),
        total_cost=('costPrice', 'sum')
    ).reset_index()

    # Calculate profit and profit margin
    low_performing_products['profit'] = low_performing_products['total_revenue'] - low_performing_products['total_cost']
    low_performing_products['profit_margin'] = (low_performing_products['profit'] / low_performing_products['total_revenue']) * 100

    # Format profit margin as a percentage with the '%' symbol
    low_performing_products['profit_margin'] = low_performing_products['profit_margin'].map(lambda x: f"{x:.2f}%")

    # Sort the DataFrame by total revenue in ascending order
    low_performing_products = low_performing_products.sort_values(by='total_revenue')

    # Filter slider for quantity sold plot
    st.sidebar.markdown("### Low performing products")
    min_quantity, max_quantity = low_performing_products['quantity_sold'].min(), low_performing_products['quantity_sold'].max()

    # Slider to select product range based on quantity sold
    quantity_range = st.sidebar.slider("Select Quantity Sold Range:", 
                                       min_value=int(min_quantity), 
                                       max_value=int(max_quantity), 
                                       value=(int(min_quantity), int(min_quantity + (max_quantity - min_quantity) * 0.10)))

    # Filter products based on selected quantity range
    filtered_products_by_quantity = low_performing_products[ 
        (low_performing_products['quantity_sold'] >= quantity_range[0]) & 
        (low_performing_products['quantity_sold'] <= quantity_range[1]) 
    ]

    # Group the filtered data by product name to avoid duplicate products
    filtered_products_by_quantity = filtered_products_by_quantity.groupby('product_name').agg({
        'quantity_sold': 'sum',
        'total_revenue': 'sum',
        'total_cost': 'sum',
        'profit': 'sum',
        'profit_margin': 'first'
    }).reset_index()

    filtered_products_by_quantity = filtered_products_by_quantity.sort_values(by='quantity_sold')

    # Move controls to the sidebar
    show_data_labels = st.sidebar.checkbox("Show Data Labels", key="data_labels_low_performing_products")
    color_scale = st.sidebar.selectbox("Select Color Scale:", 
                                        options=['Viridis', 'Cividis', 'Plasma', 'Blues'], 
                                        index=2,
                                        key="color_scale_low_performing")
    plot_type = st.sidebar.selectbox("Select Plot Type:", 
                                      options=['Bar Plot', 'Line Plot'], 
                                      index=0, 
                                      key="plot_type_low_performing")

    # # Plot Quantity Sold for filtered products
    # if plot_type == 'Bar Plot':
    #     fig_quantity_sold = px.bar(
    #         filtered_products_by_quantity,
    #         x='product_name',
    #         y='quantity_sold',
    #         title='Quantity Sold by Low Performing Products',
    #         labels={'quantity_sold': 'Quantity Sold', 'product_name': 'Product'},
    #         color='quantity_sold',  
    #         color_continuous_scale=color_scale
    #     )
    # else:
    #     fig_quantity_sold = px.line(
    #         filtered_products_by_quantity,
    #         x='product_name',
    #         y='quantity_sold',
    #         title='Quantity Sold by Low Performing Products',
    #         labels={'quantity_sold': 'Quantity Sold', 'product_name': 'Product'},
    #         markers=True
    #     )

    # if show_data_labels:
    #     fig_quantity_sold.update_traces(
    #         text=filtered_products_by_quantity['quantity_sold'], 
    #         textposition='outside'
    #     )

    # # Update the plot size to 1000 x 600
    # fig_quantity_sold.update_layout(width=1000, height=600)
    # st.plotly_chart(fig_quantity_sold, use_container_width=False)

    # Filter slider for total revenue plot
    st.sidebar.markdown("#### Total Revenue Filter")
    min_revenue, max_revenue = low_performing_products['total_revenue'].min(), low_performing_products['total_revenue'].max()

    # Slider to select product range based on total revenue
    revenue_range = st.sidebar.slider("Select Total Revenue Range:", 
                                       min_value=int(min_revenue), 
                                       max_value=int(max_revenue), 
                                       value=(int(min_revenue), int(min_revenue + (max_revenue - min_revenue) * 0.02)))

    # Filter products based on selected revenue range
    filtered_products_by_revenue = low_performing_products[ 
        (low_performing_products['total_revenue'] >= revenue_range[0]) & 
        (low_performing_products['total_revenue'] <= revenue_range[1]) 
    ]

    # Group the filtered data by product name to avoid duplicate products
    filtered_products_by_revenue = filtered_products_by_revenue.groupby('product_name').agg({
        'quantity_sold': 'sum',
        'total_revenue': 'sum',
        'total_cost': 'sum',
        'profit': 'sum',
        'profit_margin': 'first'
    }).reset_index()

    filtered_products_by_revenue = filtered_products_by_revenue.sort_values(by='total_revenue')

    if plot_type == 'Bar Plot':
        fig_total_revenue = px.bar(
            filtered_products_by_revenue,
            x='product_name',
            y='total_revenue',
            title='Total Revenue by Low Performing Products',
            labels={'total_revenue': 'Total Revenue', 'product_name': 'Product'},
            color='total_revenue',
            color_continuous_scale=color_scale
        )
    else:
        fig_total_revenue = px.line(
            filtered_products_by_revenue,
            x='product_name',
            y='total_revenue',
            title='Total Revenue by Low Performing Products',
            labels={'total_revenue': 'Total Revenue', 'product_name': 'Product'},
            markers=True
        )

    if show_data_labels:
        fig_total_revenue.update_traces(
            text=filtered_products_by_revenue['total_revenue'], 
            textposition='outside'
        )

    if filtered_products_by_quantity.empty:
        st.warning("No low performing products found within the selected quantity range.")
    if filtered_products_by_revenue.empty:
        st.warning("No low performing products found within the selected revenue range.")

    low_performing_products['total_revenue'] = low_performing_products['total_revenue'].apply(lambda x: f"{x:.2f}")
    low_performing_products['total_cost'] = low_performing_products['total_cost'].apply(lambda x: f"{x:.2f}")
    low_performing_products['profit'] = low_performing_products['profit'].apply(lambda x: f"{x:.2f}")
    

    #st.table(low_performing_products)

    @st.cache_data
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv = convert_df(low_performing_products)

    st.sidebar.download_button(
            label="Download low performing products Data",
            data=csv,   
            file_name='low_performing_products.csv',
            mime='text/csv',
        )

    # Update the plot size to 1000 x 600
    fig_total_revenue.update_layout(width=1000, height=600)
    st.plotly_chart(fig_total_revenue, use_container_width=False)
