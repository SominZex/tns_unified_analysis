import pandas as pd
import streamlit as st
import plotly.express as px

def top_n_product_analysis(store_data, all_data):
    # st.markdown("<br><br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: green; text-align: center;'>TOP-N PRODUCTS ANALYSIS</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar components
    st.sidebar.header("Top-N Products Control Panel")

    # Select a store from the store names
    store_names = store_data['storeName'].unique()
    selected_store = st.sidebar.selectbox("Select a Store:", store_names, key="store_selector_product")

    # Filter the data for the selected store
    store_data_filtered = store_data[store_data['storeName'] == selected_store]

    # Group sales by product for the selected store
    product_sales = store_data_filtered.groupby('productName').agg(
        total_sales=('totalProductPrice', 'sum'),
        total_quantity=('quantity', 'sum'),
    ).reset_index()

    total_sales_store = product_sales['total_sales'].sum()

    # Sort products by total sales and get the top N products
    unique_products = product_sales['productName'].unique()
    n_products = st.sidebar.slider("Select the number of top products to analyze:", 
                                    min_value=1, 
                                    max_value=len(unique_products), 
                                    value=50)

    top_n_products_sales = product_sales.nlargest(n_products, 'total_sales')

# Calculate sales contribution % to total sales of the selected store and round to 2 decimals
    top_n_products_sales['contribution'] = ((top_n_products_sales['total_sales'] / total_sales_store) * 100).round(2).astype(str) + '%'

    total_sales_all = all_data['totalProductPrice'].sum()

    all_product_sales = all_data.groupby('productName').agg(
        total_sales=('totalProductPrice', 'sum')
    ).reset_index()

    top_n_products_sales = top_n_products_sales.merge(
        all_product_sales,
        on='productName',
        suffixes=('', '_overall')
    )

    top_n_products_sales['company standard'] = ((top_n_products_sales['total_sales_overall'] / total_sales_all) * 100).round(2).astype(str) + '%'

    # Calculate the variance between sales_contribution_store (%) and sales_contribution_all (%) and round to 2 decimals
    top_n_products_sales['variance'] = (
        (top_n_products_sales['contribution'].str.rstrip('%').astype(float) - 
        top_n_products_sales['company standard'].str.rstrip('%').astype(float))
    ).round(2).astype(str) + '%'


    def highlight_negative(val):
        """
        Apply red text for negative values in the 'sales_contribution_variance (%)' column.
        """
        color = 'red' if '-' in val else 'black'
        return f'color: {color}'

    df_display = top_n_products_sales[['productName','total_sales','total_quantity','contribution']]
    df_display['total_sales'] = df_display['total_sales'].apply(lambda x: f"{x:.2f}")

    styled_df = df_display.style.applymap(highlight_negative, subset=['variance'])


    # User input for plot type for Top N Product Analysis
    plot_type = st.sidebar.selectbox("Select Plot Type for Top N Product Analysis:", 
                                      ["Bar Chart", "Donut Chart", "Line Chart"], 
                                      key="plot_type_product")

    # User input for color selection for product plots
    color_options_product = px.colors.named_colorscales()
    selected_color_product = st.sidebar.selectbox("Select Color Scale for Top N Product Plot:", 
                                                   color_options_product, 
                                                   key="color_scale_product")

    # User input to toggle data labels for Top N Product Analysis
    show_data_labels_product = st.sidebar.checkbox("Show Data Labels for Top N Product Analysis", 
                                                    value=True, 
                                                    key="show_data_labels_product")

    chart_width, chart_height = 1000, 600

    # Create the plot based on the selected type for Top N Product Analysis
    if plot_type == "Bar Chart":
        fig_product = px.bar(
            top_n_products_sales,
            x='productName',
            y='total_sales',
            title=f'Top {n_products} Products by Total Sales',
            labels={'total_sales': 'Total Sales', 'productName': 'Product Name'},
            color='total_sales',
            color_continuous_scale=selected_color_product
        )
        if show_data_labels_product:
            fig_product.update_traces(texttemplate='%{y:.2f}', textposition='outside')

        # Update layout with fixed width and height
        fig_product.update_layout(width=chart_width, height=chart_height)
        st.plotly_chart(fig_product, use_container_width=False)

    elif plot_type == "Donut Chart":
        fig_product = px.pie(
            top_n_products_sales,
            names='productName',
            values='total_sales',
            title=f'Top {n_products} Products by Total Sales (Donut Chart)',
            hole=0.4
        )
        if show_data_labels_product:
            fig_product.update_traces(textinfo='percent+label')

        # Update layout with fixed width and height
        fig_product.update_layout(width=chart_width, height=chart_height)
        st.plotly_chart(fig_product, use_container_width=False)

    elif plot_type == "Line Chart":
        fig_product = px.line(
            top_n_products_sales,
            x='productName',
            y='total_sales',
            title=f'Top {n_products} Products by Total Sales (Line Chart)',
            labels={'total_sales': 'Total Sales', 'productName': 'Product Name'},
            line_shape='linear'
        )
        if show_data_labels_product:
            fig_product.add_scatter(
                x=top_n_products_sales['productName'],
                y=top_n_products_sales['total_sales'],
                mode='text',
                text=top_n_products_sales['total_sales'].round(2),
                textposition='top center'
            )

        # Update layout with fixed width and height
        fig_product.update_layout(width=chart_width, height=chart_height)
        st.plotly_chart(fig_product, use_container_width=False)

    # Display the DataFrame for Top N Product Analysis
    st.table(df_display)

    @st.cache_data
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv_prod = convert_df(df_display)

    st.sidebar.download_button(
            label="Download Top-N Sales Data",
            data=csv_prod,   
            file_name='top_n_sales.csv',
            mime='text/csv',
        )

    # Plotting to compare contribution and company standard for top N products
    fig_comparison = px.line(
        top_n_products_sales, 
        x='productName', 
        y=['contribution', 'company standard'], 
        title=f'Comparison of Contribution and Company Standard for Top {n_products} Products',
        labels={'value': 'Percentage (%)', 'productName': 'Product Name'},
        line_shape='linear',
        color_discrete_map={
            'contribution': 'green',
            'company standard': 'blue'
        }
    )

    # Add traces for both contribution and company standard with custom colors
    fig_comparison.update_traces(mode='lines+markers', marker=dict(size=8))

    # Set y-axis to show percentage values
    fig_comparison.update_yaxes(ticksuffix="%")

    # Update layout with fixed width, height, and legend placement
    fig_comparison.update_layout(
        width=1000, 
        height=600, 
        legend_title_text='Metrics',
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
        
            x=1
        )
    )
    # st.markdown("<br><br><br><br><br><br>", unsafe_allow_html=True)
    # st.markdown("<h4 style='color: green; text-align: center;'>Contribution VS Company Standard</h4>", unsafe_allow_html=True)
    # Display the plot in Streamlit
    # st.plotly_chart(fig_comparison, use_container_width=False)



    product_sales_rag = store_data_filtered.groupby('productName').agg(
        total_sales=('totalProductPrice', 'sum')
    ).reset_index()


    product_sales_rag['RAG_Status'] = product_sales_rag['total_sales'].apply(
    lambda sales: 'Red' if sales < 100 else ('Amber' if sales <= 300 else 'Green')
    )

    # # ---- RAG Analysis ----
    # st.markdown("---")
    # st.markdown("<h2 style='color: green; text-align: center;'>RAG ANALYSIS BY TOTAL SALES</h2>", unsafe_allow_html=True)
    # st.markdown("---")


    rag_red = product_sales_rag[product_sales_rag['RAG_Status'] == 'Red']
    rag_red['total_sales'] = rag_red['total_sales'].apply(lambda x: f"{x:.2f}")
    rag_amber = product_sales_rag[product_sales_rag['RAG_Status'] == 'Amber']
    rag_amber['total_sales'] = rag_amber['total_sales'].apply(lambda x: f"{x:.2f}")
    rag_green = product_sales_rag[product_sales_rag['RAG_Status'] == 'Green']
    rag_green['total_sales'] = rag_green['total_sales'].apply(lambda x: f"{x:.2f}")


    csv_red = convert_df(rag_red)
    csv_amber = convert_df(rag_amber)
    csv_green = convert_df(rag_green)

    st.sidebar.download_button(
            label="Download Red Category Data",
            data=csv_red,   
            file_name='red.csv',
            mime='text/csv',
        )

    st.sidebar.download_button(
            label="Download Amber Category Data",
            data=csv_amber,   
            file_name='amber.csv',
            mime='text/csv',
        )

    st.sidebar.download_button(
            label="Download Green Category Data",
            data=csv_green,   
            file_name='red.csv',
            mime='text/csv',
        )



    st.markdown("<h4 style='color: green; text-align: center; margin-top: 0px;'>Recommendations</h4>", unsafe_allow_html=True)


    default_recommendations = (
            "- Create attractive bundles of the top selling products mentioned above which complement each other.\n"
        )


    st.markdown(
            """
            <style>
            .recommendations-textarea textarea {
                font-size: 16px !important; /* Adjust the font size here */
                line-height: 1.5 !important;
            }
            </style>
            """,
            unsafe_allow_html=True
    )


    feedback = st.text_area(
            "",
            default_recommendations,
            key="recommendations_input_day_product",
            placeholder="Write your recommendations here...",
            label_visibility="visible",
            help="Write your suggestions or adjustments related to sales categories."
        )

        # Wrap the text area with a custom class for applying styles
    st.markdown('<div class="recommendations-textarea"></div>', unsafe_allow_html=True)