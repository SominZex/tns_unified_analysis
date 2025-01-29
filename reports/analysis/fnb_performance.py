import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def fnb_performance_analysis(store_data, all_data):
    # st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: green; text-align: center;'>F&B PERFORMANCE</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # List of F&B brands to filter
    fnb_brands = ['Takeout Cafe', 'TNS', 'The New Shop', 'Urban Tapri']

    # Categories to exclude from the analysis
    categories_to_exclude = [
        'Home Cleaning', 'Others', 'Hookah', 'Art', 'Atta & Flour', 'Audio & Accessories', 'Baby Care',
        'Bath & Body', 'Bath &  Body', 'Accessories', 'Car Accessories', 'Book & Magazine', 'Boxes', 
        'Gift Boxes', 'Cigar', 'Cigarettes', 'Cloths', 'Decor', 'Decoration', 'Chhath Puja Special', 
        'Beauty Grooming Devices', 'Carry Bags', 'Condiments', 'Dhoop & Aggarbattis', 'Diabetes Care', 
        'Dips & Dressings', 'Crockery & Utensils', 'Notebooks & Diaries', 'Provisions', 
        'Fashion & Accessories', 'Fragrances', 'Disposables', 'Disposables & Tissues', 'Home Decor', 
        'Home Care', 'Kitchen', 'Laundry', 'Home & Kitchen Appliances', 'Valentine Week', 'Toys', 
        'Todler Toys', 'Tobacco', 'Skin Care', 'Sexual Wellness', 'Services', 'Raw Material', 'Rakhi', 
        'Rakhi Special', 'Pest Control', 'Personal Care', 'Pooja', 'Pooja Essentials', 'Science Kits', 
        'Health Care', 'Light Candles & Diyas', 'Light up & Diyas', 'Toilet', 'Pain Relief', 'Papers', 
        'Party', 'Party Pack', 'Oral Care', 'Learning & Motivation', 'Pen & Pencils', 'Hygiene', 
        'Interior Accessories', 'Hair Care', 'Ice Cubes', 'Havan Accessories', 'Face Care', 'Hookah'
    ]

    # Sidebar controls
    with st.sidebar:
        st.header("F&B Performance Controls")
        
        # Select a store from the store names
        store_names = store_data['storeName'].unique()
        selected_store = st.selectbox("Select a Store:", store_names, key="store_selector_fnb")

        # User input for selecting the metric for performance analysis
        metric = st.selectbox("Select Metric for F&B Performance Analysis:", 
                              ["Total Quantity", "Total Revenue", "Profit", "Profit Margin"], 
                              key="metric_selector_fnb",index=1)

        # Option to display data labels
        show_data_labels = st.checkbox("Show Data Labels", value=True, key="data_labels_fnb")

        # Choose plot type
        plot_type = st.selectbox("Select Plot Type:", ["Pie", "Bar", "Scatter"], key="plot_type_selector_fnb")

        # Choose color scale
        color_scale = st.selectbox("Select Color Scale:", 
                                   ["Viridis", "Cividis", "Plasma", "Inferno", "Magma"], 
                                   key="color_scale_fnb", index=4)

    # Filter the data for the selected store
    store_data_filtered = store_data[store_data['storeName'] == selected_store]

    # Filter the data for F&B brands
    fnb_data = store_data_filtered[store_data_filtered['brandName'].isin(fnb_brands)]

    # Exclude specific categories
    fnb_data = fnb_data[~fnb_data['categoryName'].isin(categories_to_exclude)]

    # Calculate total sales, total cost, profit, and profit margin for each brand
    fnb_performance = fnb_data.groupby('brandName').agg(
        total_quantity=('quantity', 'sum'),
        total_revenue=('totalProductPrice', 'sum'),
        total_cost=('costPrice', lambda x: (x * fnb_data.loc[x.index, 'quantity']).sum())  
    ).reset_index()

    # Calculate total sales for the selected store
    total_sales_selected_store = fnb_performance['total_revenue'].sum()

    all_fnb_data = all_data[all_data['brandName'].isin(fnb_brands)]
    all_fnb_data = all_fnb_data[~all_fnb_data['categoryName'].isin(categories_to_exclude)]

    fnb_performance['contribution'] = (fnb_performance['total_revenue'] / total_sales_selected_store) * 100

    company_benchmark = pd.read_csv('./reports/company_bechmark/fnb_benchmark.csv')

    fnb_performance = fnb_performance.merge(company_benchmark, on = "brandName", how='left')

    fnb_performance['variance'] = fnb_performance['contribution'] - fnb_performance['Company Standard']

    # Calculate profit and profit margin
    fnb_performance['profit'] = fnb_performance['total_revenue'] - fnb_performance['total_cost']
    fnb_performance['profit_margin'] = (fnb_performance['profit'] / fnb_performance['total_revenue']) * 100

    if metric == "Total Quantity":
        y_axis = 'total_quantity'
    elif metric == "Total Revenue":
        y_axis = 'total_revenue'
    elif metric == "Profit":
        y_axis = 'profit'
    elif metric == "Profit Margin":
        y_axis = 'profit_margin'

    if plot_type == "Pie":
        fig_fnb = px.pie(
            fnb_performance,
            names='brandName',
            values=y_axis,
            title=f'F&B Brands Performance by {metric}',
            color_discrete_sequence=px.colors.sequential.__dict__[color_scale],
            hole=0.3  
        )

        if show_data_labels:
            fig_fnb.update_traces(
                textinfo='label+value',
                textposition='outside',
                hovertemplate='%{label}: %{value}<extra></extra>'
            )

    elif plot_type == "Bar":
        fig_fnb = px.bar(
            fnb_performance,
            x='brandName',
            y=y_axis,
            title=f'F&B Brands Performance by {metric}',
            labels={y_axis: metric, 'brandName': 'F&B Brand'},
            color=y_axis,
            color_continuous_scale=color_scale
        )
        # Add data labels for bar plot
        if show_data_labels:
            fig_fnb.update_traces(text=fnb_performance[y_axis], textposition='outside')

    elif plot_type == "Scatter":
        fig_fnb = px.scatter(
            fnb_performance,
            x='brandName',
            y=y_axis,
            title=f'F&B Brands Performance by {metric}',
            labels={y_axis: metric, 'brandName': 'F&B Brand'},
            color=y_axis,
            color_continuous_scale=color_scale,
            size=y_axis 
        )
        if show_data_labels:
            fig_fnb.update_traces(text=fnb_performance[y_axis], textposition='top center')

    # Update layout to set specific size
    fig_fnb.update_layout(width=1000, height=600)

    # Display the plot with specified size
    st.plotly_chart(fig_fnb)

    def highlight_negative_variance(s):
        numeric_values = pd.to_numeric(s, errors='coerce')
        return ['background-color: red' if v < 0 else '' for v in numeric_values]

    fnb_performance['contribution'] = fnb_performance['contribution'].map(lambda x: f"{x:.2f}%")
    fnb_performance['Company Standard'] = fnb_performance['Company Standard'].map(lambda x: f"{x:.2f}%")
    fnb_performance['profit_margin'] = fnb_performance['profit_margin'].map(lambda x: f"{x:.2f}%")
    fnb_performance['profit'] = fnb_performance['profit'].map(lambda x: f"{x:.2f}")
    fnb_performance['total_revenue'] = fnb_performance['total_revenue'].map(lambda x: f"{x:.2f}")
    fnb_performance['total_cost'] = fnb_performance['total_cost'].map(lambda x: f"{x:.2f}")
    fnb_performance['variance_str'] = fnb_performance['variance'].map(lambda x: f"{x:.2f}%" if x >= 0 else f"-{abs(x):.2f}%")

    variance_highlight = fnb_performance['variance']
    highlighted_variance = highlight_negative_variance(variance_highlight)

    st.table(
        fnb_performance[['brandName', 'total_revenue', 'total_cost', 'profit', 'profit_margin', 'contribution', 'Company Standard', 'variance']].style.apply(highlight_negative_variance, subset=['variance'])
    )

    @st.cache_data
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv_fnb = convert_df(fnb_performance)

    st.sidebar.download_button(
            label="Download FnB Sales Data",
            data=csv_fnb,   
            file_name='fnb_sales.csv',
            mime='text/csv',
        )

    fnb_performance['contribution_float'] = pd.to_numeric(fnb_performance['contribution'].astype(str).str.rstrip('%'), errors='coerce')
    fnb_performance['Company Standard_float'] = pd.to_numeric(fnb_performance['Company Standard'].astype(str).str.rstrip('%'), errors='coerce')

    # Line chart for contribution vs Company Standard
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=fnb_performance['brandName'], 
        y=fnb_performance['contribution_float'], 
        mode='lines+markers', 
        name='Contribution', 
        line=dict(color='blue')
    ))

    fig_line.add_trace(go.Scatter(
        x=fnb_performance['brandName'], 
        y=fnb_performance['Company Standard_float'], 
        mode='lines+markers', 
        name='Company Standard', 
        line=dict(color='green')
    ))

    fig_line.update_layout(
        title='Contribution vs Company Standard',
        xaxis_title='Brand Name',
        yaxis_title='Percentage',
        height=600,
        width=1000
    )

    st.plotly_chart(fig_line)

    st.markdown("<h4 style='color: green; text-align: center; margin-top: 0px;'>Recommendations</h4>", unsafe_allow_html=True)

    default_recommendations = (
            "- Market more about the F&B products by offering them at the cash counters while billing.\n"
        )
        # Custom CSS to enlarge the text area font size
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

        # Text area with larger font size
    feedback = st.text_area(
            "",
            default_recommendations,
            key="recommendations_input_day_product_fnb",
            placeholder="Write your recommendations here...",
            label_visibility="visible",
            help="Write your suggestions or adjustments related to sales categories."
        )

        # Wrap the text area with a custom class for applying styles
    st.markdown('<div class="recommendations-textarea"></div>', unsafe_allow_html=True)
