import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

def analyze_monetized_brands(store_data, all_data):
    # st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: green; text-align: center;'>📈 MONETIZED BRANDS PERFORMANCE</h4>", unsafe_allow_html=True)
    st.markdown("---")
    
    # List of brands to filter
    brands_to_select = [
        "Bazana", "Pokka", "Panash", "Morning Fresh", "ITC Master Chef",
        "Havmor", "HUFT", "Rtb Kombucha", "Wow Momo", "Vegan-Day",
        "UE Boost", "Moon", "Continental", "Nutriburst", "Runway",
        "Vadilal", "Pure Temptation", "Rebound", "3 Sisters",
        "Whiskers", "Burf", "AMRIT FOOD", "Growfitz", "Aplomb",
        "Sanfe", "Griesmore", "Alphadent", "Clove"
    ]

    # Sidebar inputs for filtering
    st.sidebar.markdown("### Filters for monetized brands")
    store_names = store_data['storeName'].unique()
    selected_store = st.sidebar.selectbox("Select a Store:", store_names, key="store_selector_monetized")
    metric = st.sidebar.selectbox("Select Metric for Monetized Brands Analysis:", 
                                  ["Total Quantity", "Total Revenue", "Profit", "Profit Margin"], 
                                  key="metric_selector_monetized")
    show_data_labels = st.sidebar.checkbox("Show Data Labels", value=True, key="data_labels_monetized")
    plot_type = st.sidebar.selectbox("Select Plot Type:", ["Bar", "Scatter", "Pie"], key="plot_type_selector_monetized")
    color_scale = st.sidebar.selectbox("Select Color Scale:", 
                                       ["Viridis", "Cividis", "Plasma", "Inferno", "Magma"], 
                                       key="color_scale_monetized")

    # Filter data for the selected store and the chosen brands
    store_data_filtered = store_data[store_data['storeName'] == selected_store]
    filtered_brands_store = store_data_filtered[store_data_filtered['brandName'].isin(brands_to_select)]

    # Calculate total sales for the selected store and all data
    total_sales_store = store_data_filtered['totalProductPrice'].sum()
    #total_sales_all_data = all_data['totalProductPrice'].sum()

    # Filter all data for the specified brands
    #filtered_brands_all = all_data[all_data['brandName'].isin(brands_to_select)]

    if not filtered_brands_store.empty:
        # Aggregate monetized performance for the selected store
        monetized_performance_store = filtered_brands_store.groupby('brandName').agg(
            total_quantity=('quantity', 'sum'),
            total_revenue=('totalProductPrice', 'sum'),
            total_cost=('costPrice', 'sum'),
            total_products=('productId', 'nunique')
        ).reset_index()

        # Calculate profit and profit margin for the selected store
        monetized_performance_store['profit'] = monetized_performance_store['total_revenue'] - monetized_performance_store['total_cost']
        monetized_performance_store['profit_margin'] = (monetized_performance_store['profit'] / monetized_performance_store['total_revenue']) * 100

        # Calculate sales contribution % of each monetized brand to the total sales of the selected store
        monetized_performance_store['contribution'] = (monetized_performance_store['total_revenue'] / total_sales_store) * 100

        # Aggregate monetized performance for all data
        # monetized_performance_all = filtered_brands_all.groupby('brandName').agg(
        #     total_quantity=('quantity', 'sum'),
        #     total_revenue=('totalProductPrice', 'sum')
        # ).reset_index()

        company_benchmark = pd.read_csv('./reports/company_bechmark/monetized_brands.csv')

        # monetized_performance_all = monetized_performance_all.merge(company_benchmark, on="brandName", how = "left")
        # Calculate sales contribution % of each monetized brand to the total sales of all data
        # Merge the dataframes for store and all data contributions
        monetized_performance_store = pd.merge(monetized_performance_store, company_benchmark[['brandName', 'Company Standard']], on='brandName', how='left')

        # Calculate the variance
        monetized_performance_store["variance"] = monetized_performance_store['contribution'] - monetized_performance_store['Company Standard']

        # Determine y-axis based on selected metric
        if metric == "Total Quantity":
            y_axis = 'total_quantity'
        elif metric == "Total Revenue":
            y_axis = 'total_revenue'
        elif metric == "Profit":
            y_axis = 'profit'
        elif metric == "Profit Margin":
            y_axis = 'profit_margin'

        # Generate the appropriate plot based on user selection
        if plot_type == "Bar":
            fig_monetized = px.bar(
                monetized_performance_store,
                x='brandName',
                y=y_axis,
                title=f'Monetized Brands Performance by {metric}',
                labels={y_axis: metric, 'brandName': 'Monetized Brand'},
                color=y_axis,
                color_continuous_scale=color_scale
            )
            if show_data_labels:
                fig_monetized.update_traces(text=monetized_performance_store[y_axis], textposition='outside')

        elif plot_type == "Scatter":
            fig_monetized = px.scatter(
                monetized_performance_store,
                x='brandName',
                y=y_axis,
                title=f'Monetized Brands Performance by {metric}',
                labels={y_axis: metric, 'brandName': 'Monetized Brand'},
                color=y_axis,
                color_continuous_scale=color_scale,
                size=y_axis 
            )
            if show_data_labels:
                fig_monetized.update_traces(text=monetized_performance_store[y_axis], textposition='top center')

        elif plot_type == "Pie":
            fig_monetized = px.pie(
                monetized_performance_store,
                names='brandName',
                values=y_axis,
                title=f'Monetized Brands Performance by {metric}',
                color_discrete_sequence=px.colors.sequential.__dict__[color_scale],
                hole=0.3
            )
            if show_data_labels:
                fig_monetized.update_traces(textinfo='label+percent', textposition='inside')

        # Display the plot
        fig_monetized.update_layout(width=1000, height=600)
        st.plotly_chart(fig_monetized)

        # Format profit margin and sales contribution as percentages
        monetized_performance_store['profit_margin'] = monetized_performance_store['profit_margin'].map(lambda x: f"{x:.2f}%")
        monetized_performance_store['contribution'] = monetized_performance_store['contribution'].map(lambda x: f"{x:.2f}%")
        monetized_performance_store['Company Standard'] = monetized_performance_store['Company Standard'].map(lambda x: f"{x:.2f}%")
        monetized_performance_store['variance'] = monetized_performance_store['variance'].map(lambda x: f"{x:.2f}%")

        # Highlight negative variance
        def highlight_negative(val):
            try:
                val_float = float(val.replace('%', ''))
                if val_float < 0:
                    return 'background-color: red; color: white'
            except ValueError:
                return ''
            return ''
        
        monetized_performance_store['total_revenue'] = monetized_performance_store['total_revenue'].apply(lambda x: f"{x:.2f}")
        monetized_performance_store['total_cost'] = monetized_performance_store['total_cost'].apply(lambda x: f"{x:.2f}")
        monetized_performance_store['profit'] = monetized_performance_store['profit'].apply(lambda x: f"{x:.2f}")
        styled_df = monetized_performance_store[['brandName', 'total_revenue', 'total_cost', 'profit', 'profit_margin', 'contribution', 'Company Standard', 'variance']].style.applymap(
                     highlight_negative, subset=['variance']
                    )

        st.table(styled_df)

        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')

        csv_monetized = convert_df(monetized_performance_store)

        st.sidebar.download_button(
                label="Download monetized brands Data",
                data=csv_monetized,   
                file_name='monetized_brands.csv',
                mime='text/csv',
            )

        # New Line Plot for Contribution vs Company Standard
        monetized_performance_store['contribution_numeric'] = monetized_performance_store['contribution'].str.replace('%', '').astype(float)
        monetized_performance_store['company_standard_numeric'] = monetized_performance_store['Company Standard'].str.replace('%', '').astype(float)

        line_fig = px.line(
            monetized_performance_store,
            x='brandName',
            y=['contribution_numeric', 'company_standard_numeric'],
            title='Contribution vs Company Standard',
            labels={'value': 'Percentage', 'brandName': 'Brand Name'},
            markers=True,
            color_discrete_sequence=['green', 'blue'] 
        )
        
        # Customize y-axis to display percentages
        line_fig.update_yaxes(tickvals=np.arange(0, 101, 10), ticktext=[f"{i}%" for i in range(0, 101, 10)])
        
        line_fig.update_layout(width=1000, height=500)

        st.plotly_chart(line_fig)

    else:
        st.warning("No data available for the selected brands.")

    missing_brands = set(brands_to_select) - set(filtered_brands_store['brandName'].unique())
    if missing_brands:
        # Create a DataFrame for the missing brands
        st.markdown("<h4 style='color: red; text-align: center;'>Missing monetized Brands</h4>", unsafe_allow_html=True)
        missing_brands_df = pd.DataFrame(list(missing_brands), columns=['Missing Monetized Brands'])
        st.table(missing_brands_df) 

    st.markdown("<h4 style='color: green; text-align: center; margin-top: 0px;'>Recommendations</h4>", unsafe_allow_html=True)

        # Default recommendations
    default_recommendations = (
            "- Should start keeping the stock of the above-mentioned brands as they also provide monetization benefits\n"
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
            key="recommendations_input_day_monetized",
            placeholder="Write your recommendations here...",
            label_visibility="visible",
            help="Write your suggestions or adjustments related to sales categories."
        )

        # Wrap the text area with a custom class for applying styles
    st.markdown('<div class="recommendations-textarea"></div>', unsafe_allow_html=True)
