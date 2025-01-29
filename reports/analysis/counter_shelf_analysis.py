import pandas as pd
import streamlit as st
import plotly.express as px

def analyze_counter_shelf_products(store_data, all_data): 
    st.markdown("<h4 style='color: green; text-align: center;'>COUNTER SHELF PRODUCTS ANALYSIS</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # List of counter shelf product categories to filter
    counter_shelf_categories = [
        "Candies & Toffees", 
        "Sweets, Chocolates & Candies", 
        "Chocolates", 
        "Gums, Mints & Mouth Freshener"
    ]

    st.sidebar.markdown("## Filter Options for counter shelf")

    store_names = store_data['storeName'].unique()
    selected_store = st.sidebar.selectbox("Select a Store:", store_names, key="store_selector_counter_shelf")

    metric = st.sidebar.selectbox("Select Metric for Counter Shelf Products Analysis:", 
                                  ["Total Quantity", "Total Revenue", "Profit", "Profit Margin"], 
                                  key="metric_selector_counter_shelf")

    # Option to display data labels in the sidebar
    show_data_labels = st.sidebar.checkbox("Show Data Labels", value=True, key="data_labels_counter_shelf")

    # Choose plot type, set default to "Pie" in the sidebar
    plot_type = st.sidebar.selectbox("Select Plot Type:", ["Bar", "Scatter", "Pie"], key="plot_type_selector_counter_shelf", index=0)

    # Choose color scale in the sidebar
    color_scale = st.sidebar.selectbox("Select Color Scale:", 
                                       ["Viridis", "Cividis", "Plasma", "Inferno", "Magma"], 
                                       key="color_scale_counter_shelf")

    store_data_filtered = store_data[store_data['storeName'] == selected_store]

    filtered_counter_shelf = store_data_filtered[store_data_filtered['categoryName'].isin(counter_shelf_categories)]

    missing_categories = set(counter_shelf_categories) - set(filtered_counter_shelf['categoryName'].unique())

    if not filtered_counter_shelf.empty:

        counter_shelf_performance = filtered_counter_shelf.groupby('categoryName').agg(
            total_quantity=('quantity', 'sum'),
            total_revenue=('totalProductPrice', 'sum'),
            total_cost=('costPrice', lambda x: (x * filtered_counter_shelf.loc[x.index, 'quantity']).sum()), 
            total_products=('productId', 'nunique') 
        ).reset_index()

        counter_shelf_performance['profit'] = counter_shelf_performance['total_revenue'] - counter_shelf_performance['total_cost']
        counter_shelf_performance['profit_margin'] = (counter_shelf_performance['profit'] / counter_shelf_performance['total_revenue']) * 100

        total_store_revenue = store_data_filtered['totalProductPrice'].sum()
        counter_shelf_performance['contribution'] = (counter_shelf_performance['total_revenue'] / total_store_revenue) * 100

        company_benchmark = pd.read_csv('./reports/company_bechmark/counter_shelf_benchmark.csv')

        counter_shelf_performance = counter_shelf_performance.merge(company_benchmark, on='categoryName', how='left')

        counter_shelf_performance['variance'] = counter_shelf_performance['contribution']-counter_shelf_performance['Company Standard']

        if metric == "Total Quantity":
            y_axis = 'total_quantity'
        elif metric == "Total Revenue":
            y_axis = 'total_revenue'
        elif metric == "Profit":
            y_axis = 'profit'
        elif metric == "Profit Margin":
            y_axis = 'profit_margin'

        if plot_type == "Bar":
            fig_counter_shelf = px.bar(
                counter_shelf_performance,
                x='categoryName',
                y=y_axis,
                title=f'Counter Shelf Products Performance by {metric}',
                labels={y_axis: metric, 'categoryName': 'Counter Shelf Category'},
                color=y_axis,
                color_continuous_scale=color_scale
            )
            # Add data labels for bar plot
            if show_data_labels:
                fig_counter_shelf.update_traces(text=counter_shelf_performance[y_axis], textposition='outside')

        elif plot_type == "Scatter":
            fig_counter_shelf = px.scatter(
                counter_shelf_performance,
                x='categoryName',
                y=y_axis,
                title=f'Counter Shelf Products Performance by {metric}',
                labels={y_axis: metric, 'categoryName': 'Counter Shelf Category'},
                color=y_axis,
                color_continuous_scale=color_scale,
                size=y_axis
            )
            # Add data labels for scatter plot
            if show_data_labels:
                fig_counter_shelf.update_traces(text=counter_shelf_performance[y_axis], textposition='top center')

        elif plot_type == "Pie":
            fig_counter_shelf = px.pie(
                counter_shelf_performance,
                names='categoryName',
                values=y_axis,
                title=f'Counter Shelf Products Performance by {metric}',
                color_discrete_sequence=px.colors.sequential.__dict__[color_scale],
                hole=0.3 
            )

            if show_data_labels:
                fig_counter_shelf.update_traces(textinfo='label+percent', textposition='outside')

        fig_counter_shelf.update_layout(width=1000, height=700)

        st.plotly_chart(fig_counter_shelf)

        counter_shelf_performance['profit_margin'] = counter_shelf_performance['profit_margin'].map(lambda x: f"{x:.2f}%")
        counter_shelf_performance['contribution'] = counter_shelf_performance['contribution'].map(lambda x: f"{x:.2f}%")
        counter_shelf_performance['Company Standard'] = counter_shelf_performance['Company Standard'].map(lambda x: f"{x:.2f}%")
        counter_shelf_performance['variance'] = counter_shelf_performance['variance'].map(lambda x: f"{x:.2f}%")
        counter_shelf_performance['total_revenue'] = counter_shelf_performance['total_revenue'].apply(lambda x: f"{x:.2f}")
        counter_shelf_performance['total_cost'] = counter_shelf_performance['total_cost'].apply(lambda x: f"{x:.2f}")
        counter_shelf_performance['profit'] = counter_shelf_performance['profit'].apply(lambda x: f"{x:.2f}")

        def highlight_negative(s):
            return ['background-color: red' if float(val.replace('%', '')) < 0 else '' for val in s]

        to_display = counter_shelf_performance[['categoryName', 'total_revenue', 'total_cost', 'profit','contribution','Company Standard','variance']]

        styled_df = to_display.style.apply(highlight_negative, subset=['variance'])

        st.table(styled_df)

        melted_df = counter_shelf_performance.melt(
            id_vars='categoryName', 
            value_vars=['contribution', 'Company Standard'], 
            var_name='Metric', 
            value_name='Percentage'
        )

        melted_df['Percentage'] = melted_df['Percentage'].apply(lambda x: float(x.replace('%', '')))
        melted_df['Percentage_label'] = melted_df['Percentage'].apply(lambda x: f'{x:.2f}%')

        fig_comparison = px.bar(
            melted_df,
            x='categoryName',
            y='Percentage',
            color='Metric',
            barmode='group',
            title="Comparison of Contribution and Company Standard by Category",
            labels={'Percentage': 'Percentage (%)', 'categoryName': 'Counter Shelf Category'},
            text='Percentage_label' 
        )

        fig_comparison.update_layout(width=1000, height=600)

        st.plotly_chart(fig_comparison)


    else:
        st.warning("No data available for the selected categories.")
    
    if missing_categories:
        st.info("Missing categories in the dataset:")
        st.write(missing_categories)

    st.markdown("<h4 style='color: green; text-align: center; margin-top: 0px;'>Recommendations</h4>", unsafe_allow_html=True)

    default_recommendations = (
            "- You’re doing good as per counter shelf products, keep it up!\n"
            "- Gather feedback from customers to understand their preferences and reasons for not purchasing these brands.\n"
            "- Use attractive signage to draw attention to these brands.\n"
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
            key="recommendations_input_counter",
            placeholder="Write your recommendations here...",
            label_visibility="visible",
            help="Write your suggestions or adjustments related to sales categories."
        )

    st.markdown('<div class="recommendations-textarea"></div>', unsafe_allow_html=True)
