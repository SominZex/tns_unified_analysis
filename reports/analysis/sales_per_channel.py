import pandas as pd
import streamlit as st
import plotly.express as px

def sales_per_channel_analysis(store_data_filtered, data, selected_store=None):
    # ---- Sales per Channel Analysis ----
    st.markdown("<br><br><br><br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: green; text-align: center;'>📊 SALES PER CHANNEL</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # Filter data for the selected store if provided
    if selected_store:
        store_data_filtered = store_data_filtered[store_data_filtered['store'] == selected_store]

    channel_sales = store_data_filtered.groupby('orderType').agg(
        total_sales=('totalProductPrice', 'sum'),
        total_quantity=('quantity', 'sum'),
        total_cost_price_raw=('costPrice', 'sum'),  # Keep raw cost price for reference
    ).reset_index()

    channel_sales['total_cost_price'] = store_data_filtered.groupby('orderType').apply(
        lambda x: (x['costPrice'] * x['quantity']).sum()
    ).values

    # Calculate total profit for each channel
    channel_sales['total_profit'] = channel_sales['total_sales'] - channel_sales['total_cost_price']

    # Check for zero quantity before calculating AOV
    if channel_sales['total_quantity'].eq(0).any():
        st.warning("Some channels have a total quantity of zero. Average Order Value may not be calculable.")

    channel_sales['average_order_value'] = channel_sales['total_sales'] / channel_sales['total_quantity'].replace(0, 1)
    channel_sales['profit_margin'] = (channel_sales['total_profit'] / channel_sales['total_sales'].replace(0, 1)) * 100

    # Calculate percentage contribution of each channel to the total sales
    channel_sales['sales_percentage_contribution'] = (channel_sales['total_sales'] / channel_sales['total_sales'].sum()) * 100
    channel_sales['sales_percentage_contribution'] = channel_sales['sales_percentage_contribution'].apply(lambda x: f"{x:.2f}%")

    # Check if the channel_sales DataFrame is empty
    if channel_sales.empty:
        st.warning("No sales data available for this analysis.")
        return None, None, None

    # Define company standards for each channel
    company_standards = {
        'tns-app': 5,
        'ondc': 2,
        'zomato': 5,
        'swiggy': 3,
        'pos': 85
    }

    # Calculate the contribution for comparison
    channel_sales['contribution'] = (channel_sales['total_sales'] / channel_sales['total_sales'].sum()) * 100

    # Create comparison DataFrame
    comparison_data = []
    for channel in company_standards.keys():
        if channel in channel_sales['orderType'].values:
            total_sales = channel_sales[channel_sales['orderType'] == channel]['total_sales'].values[0]
            contribution = channel_sales[channel_sales['orderType'] == channel]['contribution'].values[0]
            standard = company_standards[channel]
            variance = contribution - standard
            comparison_data.append({
                'Channel': channel,
                'Total Sales': total_sales,
                'Contribution': f"{contribution:.2f}%",
                'Standard': f"{standard:.2f}%",
                'Variance': f"{variance:.2f}%",
            })
        else:
            comparison_data.append({
                'Channel': channel,
                'Total Sales': 0,
                'Contribution': "0.00%",
                'Standard': f"{company_standards[channel]:.2f}%",
                'Variance': f"{-company_standards[channel]:.2f}%",
            })

    comparison_df = pd.DataFrame(comparison_data)

    # Dynamically create columns based on the number of channels
    num_channels = len(channel_sales)
    columns = st.columns(num_channels)

    # CSS for smaller, centered boxes
    st.markdown(
        """
        <style>
        .small-box {
            width: 300px; /* Smaller box width */
            margin: 0 auto; /* Center align the box */
            border: 2px solid #4CAF50;
            border-radius: 10px;
            padding: 15px;
            margin-top: 10px;
        }
        </style>
        """, 
        unsafe_allow_html=True
    )

    # Display each channel's KPIs in a separate column
    kpi_html = ""
    for index, row in channel_sales.iterrows():
        kpi_html += f"""
            <div class="small-box">
                <h4 style='text-align: center; color: #4CAF50;'>Channel: {row['orderType']}</h4>
                <p><strong>Total Sales:</strong> ₹{row['total_sales']:,}</p>
                <p><strong>Total Quantity Sold:</strong> {row['total_quantity']}</p>
                <p><strong>Total Profit:</strong> ₹{row['total_profit']:,}</p>
                <p><strong>Average Order Value (AOV):</strong> ₹{row['average_order_value']:,.2f}</p>
                <p><strong>Profit Margin:</strong> {row['profit_margin']:.2f}%</p>
                <p><strong>Sales % Contribution:</strong> {row['sales_percentage_contribution']}</p>
            </div>
        """
        with columns[index]:
            st.markdown(f"""
                <div class="small-box">
                    <h4 style='text-align: center; color: #4CAF50;'>Channel: {row['orderType']}</h4>
                    <p><strong>Total Sales:</strong> ₹{row['total_sales']:,}</p>
                    <p><strong>Total Quantity Sold:</strong> {row['total_quantity']}</p>
                    <p><strong>Total Profit:</strong> ₹{row['total_profit']:,}</p>
                    <p><strong>Average Order Value (AOV):</strong> ₹{row['average_order_value']:,.2f}</p>
                    <p><strong>Profit Margin:</strong> {row['profit_margin']:.2f}%</p>
                    <p><strong>Sales % Contribution:</strong> {row['sales_percentage_contribution']}</p>
                </div>
            """, unsafe_allow_html=True)

    channel_plot_type = st.sidebar.selectbox("Select Plot Type for Sales per Channel Analysis:", ["Bar Chart", "Donut Chart", "Line Chart"], key="channel_plot_type")

    # User input for color selection for channel plots
    selected_channel_color = st.sidebar.selectbox("Select Color Scale for Channel Plot:", ['Viridis', 'Plasma', 'Inferno', 'Magma', 'Cividis'], key="channel_color_scale")

    # User input to toggle data labels for Sales per Channel Analysis
    show_data_labels_channel = st.sidebar.checkbox("Show Data Labels for Sales per Channel Analysis", value=True, key="show_data_labels_channel")

    # Create the plot based on the selected type for Sales per Channel Analysis
    if channel_plot_type == "Bar Chart":
        fig_channel = px.bar(
            channel_sales,
            x='orderType',
            y='total_sales',
            title='Total Sales by Channel',
            labels={'total_sales': 'Total Sales', 'orderType': 'Sales Channel'},
            color='total_sales', 
            color_continuous_scale=selected_channel_color 
        )
        if show_data_labels_channel:
            fig_channel.update_traces(texttemplate='%{y:.2f}', textposition='outside')

    elif channel_plot_type == "Donut Chart":
        fig_channel = px.pie(
            channel_sales,
            names='orderType',
            values='total_sales',
            title='Total Sales by Channel',
            hole=0.4 
        )
        if show_data_labels_channel:
            fig_channel.update_traces(textinfo='percent+label')

    elif channel_plot_type == "Line Chart":
        fig_channel = px.line(
            channel_sales,
            x='orderType',
            y='total_sales',
            title='Total Sales by Channel',
            labels={'total_sales': 'Total Sales', 'orderType': 'Sales Channel'},
            line_shape='linear'
        )

        if show_data_labels_channel:
            fig_channel.add_scatter(
                x=channel_sales['orderType'],
                y=channel_sales['total_sales'],
                mode='text',
                text=channel_sales['total_sales'].round(2),
                textposition='top center'
            )

    fig_channel.update_layout(
        width=1000,
        height=600
    )

    # Display the plot with the updated layout size
    #st.plotly_chart(fig_channel)


    # Display the updated DataFrame with percentage contribution
    st.dataframe(channel_sales)

    comparison_df['Total Sales'] = comparison_df['Total Sales'].apply(lambda x: f"{x:.2f}")
    # Create styled DataFrame for comparison
    styled_comparison_df = comparison_df.style.applymap(
        lambda x: 'color: red;' if isinstance(x, str) and x.endswith('%') and float(x[:-1]) < 0 else '',
        subset=['Variance']
    )

    # Convert the styled DataFrame to HTML
    comparison_html = styled_comparison_df.to_html()

    # Display the comparison DataFrame in a centered div
    st.markdown(f'<div style="display: flex; justify-content: center; overflow-x: auto;">{comparison_html}</div>', unsafe_allow_html=True)

       # Comment or recommendation box with pre-typed recommendations
    st.markdown("<h4 style='color: green; text-align: center; margin-top: 0px;'>Recommendations</h4>", unsafe_allow_html=True)

        # Default recommendations
    default_recommendations = (
            "- Increase the sales by utilizing services like Zomato.\n"
            "- Market more about the TNS-APP to increase app orders.\n"
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
            key="recommendations_input_day_channel",
            placeholder="Write your recommendations here...",
            label_visibility="visible",
            help="Write your suggestions or adjustments related to sales categories."
        )
    # Return charts, dataframes, and KPIs
    return fig_channel, channel_sales, kpi_html

