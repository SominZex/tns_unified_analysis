import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


def time_slot_analysis(store_data, all_data):

    st.markdown("<h4 style='color: green; text-align: center;'>⏰ TIME SLOT ANALYSIS</h4>", unsafe_allow_html=True)
    st.markdown("<hr style='border-top: 2px solid #bbb;'>", unsafe_allow_html=True)

    results = {
        'charts': {},
        'dataframes': {},
        'kpis': {}
    }

    with st.sidebar:
        store_names = store_data['storeName'].unique()
        selected_store = st.selectbox("Select a Store:", store_names, key="store_selector_time")
        results['selected_store'] = selected_store

        time_plot_type = st.selectbox("Select Plot Type for Time Slot Analysis:", ["Bar Chart", "Line Chart"], index=0, key="plot_type_time")
        sort_order = st.selectbox("Select Sorting Order:", ["Ascending", "Descending"], key="sort_order_time")

        color_options_time = px.colors.named_colorscales()
        selected_color_time = st.selectbox("Select Color Scale for Time Slot Plot:", color_options_time, key="color_scale_time")
        show_data_labels_time = st.checkbox("Show Data Labels for Time Slot Analysis", value=True, key="show_data_labels_time")

    def parse_time_robust(time_str):
        if pd.isna(time_str):
            return None
        
        time_str = str(time_str).strip()

        # Remove timezone (.00Z or other formats) and milliseconds
        if '.' in time_str:
            time_str = time_str.split('.')[0]
        
        # Remove any potential timezone markers like 'Z', 'GMT', etc.
        time_str = time_str.replace('Z', '').replace('GMT', '').strip()

        # List of possible time formats to handle different time representations
        time_formats = [
            '%H:%M:%S',
            '%H:%M',
            '%I:%M:%S %p',
            '%I:%M %p',
            '%H%M%S',
            '%H%M'
        ]

        # Try parsing the time with each format
        for fmt in time_formats:
            try:
                parsed_time = datetime.strptime(time_str, fmt)
                return parsed_time.time()
            except ValueError:
                continue
        
        return None

    try:
        # Apply the robust time parsing function to the 'time' column
        store_data['parsed_time'] = store_data['time'].apply(parse_time_robust)
        
        # Convert the parsed time to a datetime object for further processing
        store_data['time'] = pd.to_datetime(store_data['parsed_time'].astype(str), format='%H:%M:%S', errors='coerce')
        
        # Drop the 'parsed_time' column since it's no longer needed
        store_data = store_data.drop('parsed_time', axis=1)

        # Extract the hour from the 'time' column
        store_data['hour'] = store_data['time'].dt.hour

        # Check if parsed time is valid
        if store_data['time'].isnull().all():
            st.warning("No valid time data available for the selected store.")
            return results

        # Check for NaN in storeName column
        store_data = store_data.dropna(subset=['storeName'])

        # Filter data for the selected store
        store_data_filtered = store_data[store_data['storeName'] == selected_store]
        
        # Check if filtered data is empty
        if store_data_filtered.empty:
            st.warning(f"No data available for the selected store: {selected_store}.")
            return results

        # Continue with the analysis after ensuring valid data is available
        store_data_filtered['orderDate'] = pd.to_datetime(store_data_filtered['orderDate'], errors='coerce')

    except Exception as e:
        st.error(f"Error in time parsing or filtering: {str(e)}")
        return results

    # Check if valid time data is available after parsing
    if store_data['time'].isnull().all():
        st.warning("No valid time data available for the selected store.")
        return results

    # Filter data for the selected store
    store_data_filtered = store_data[store_data['storeName'] == selected_store]

    # Check if any data is available for the selected store
    if store_data_filtered.empty:
        st.warning("No data available for the selected store.")
        return results

    # Continue with the analysis after ensuring valid data is available
    store_data_filtered['orderDate'] = pd.to_datetime(store_data_filtered['orderDate'], errors='coerce')



    # ---- Hourly Sales Analysis ----
    st.markdown("<h4 style='color: green; text-align: center;'>Hourly Sales</h4>", unsafe_allow_html=True)

    if store_data_filtered['time'].isnull().all():
        st.warning("No valid time data available for the selected store.")
        return results

    store_data_filtered['hour'] = store_data_filtered['time'].dt.hour

    sales_by_hour = store_data_filtered.groupby('hour').agg(
        total_sales=('totalProductPrice', 'sum'),
        total_cost_price=('costPrice', lambda x: (x * store_data_filtered.loc[x.index, 'quantity']).sum()),
        total_quantity=('quantity', 'sum'),
    ).reset_index()

    # Round total_sales, total_cost_price, and total_profit to 2 decimals
    sales_by_hour['total_sales'] = sales_by_hour['total_sales'].round(2)
    sales_by_hour['total_cost_price'] = sales_by_hour['total_cost_price'].round(2)
    sales_by_hour['total_profit'] = (sales_by_hour['total_sales'] - sales_by_hour['total_cost_price']).round(2)

    if sales_by_hour.empty:
        st.warning("No sales data available for the selected store in this time range.")
        return results

    # Calculate the total sales for the selected store
    store_total_sales = sales_by_hour['total_sales'].sum()

    # Load company benchmark data
    company_benchmark = pd.read_csv('./reports/company_bechmark/hourly_sales_benchmark.csv')

    # Contribution percentage of each hour's sales to the total sales of the selected store
    sales_by_hour['contribution'] = (sales_by_hour['total_sales'] / store_total_sales) * 100


    all_data['time'] = pd.to_datetime(all_data['time'], errors='coerce')
    all_data['hour'] = all_data['time'].dt.hour

   # Group entire dataset by hour for all stores
    # sales_by_hour_all_stores = all_data.groupby('hour').agg(
    #     total_sales_all=('totalProductPrice', 'sum')
    # ).reset_index()

    # # Calculate total sales for all stores
    # total_sales_all_stores = all_data['totalProductPrice'].sum()

    # # Calculate the contribution of each hour's sales to the total sales of all stores
    # sales_by_hour_all_stores['Company Standard'] = (sales_by_hour_all_stores['total_sales_all'] / total_sales_all_stores) * 100
    company_benchmark['hour_24'] = pd.to_datetime(company_benchmark['hour'], format='%I:%M %p').dt.hour


    sales_by_hour['hour'] = sales_by_hour['hour'].astype(int)

    # Merge store-specific and total sales data on the hour
    sales_by_hour = pd.merge(sales_by_hour, company_benchmark, left_on='hour', right_on='hour_24', how='left')

    # Variance calculation
    sales_by_hour['variance'] = (sales_by_hour['contribution'] - sales_by_hour['Company Standard'])/sales_by_hour['Company Standard']

        # Round and format contributions, company standard, and variance
    sales_by_hour['contribution'] = sales_by_hour['contribution'].round(2).astype(str) + '%'
    sales_by_hour['Company Standard'] = sales_by_hour['Company Standard'].round(2).astype(str) + '%'
    sales_by_hour['variance'] = sales_by_hour['variance'].round(2).astype(str) + '%'

    # Round total_sales, total_cost_price, total_profit to 2 decimals for display
    sales_by_hour['total_sales'] = sales_by_hour['total_sales'].map("{:.2f}".format)
    sales_by_hour['total_cost_price'] = sales_by_hour['total_cost_price'].map("{:.2f}".format)
    sales_by_hour['total_profit'] = sales_by_hour['total_profit'].map("{:.2f}".format)


    sales_by_hour['hour_12'] = sales_by_hour['hour_24'].apply(lambda x: f"{x % 12 or 12} {'AM' if x < 12 else 'PM'}")

    hour_plot_type = st.sidebar.selectbox("Select Plot Type for Hourly Sales Analysis:", ["Line Chart", "Bar Chart"], index=1, key="hour_plot_type")

    selected_hour_color = st.sidebar.selectbox("Select Color Scale for Hourly Plot:", color_options_time, key="hour_color_scale")

    show_data_labels_hour = st.sidebar.checkbox("Show Data Labels for Hourly Sales Analysis", value=True, key="show_data_labels_hour")

    # Create the plot based on the selected type for Hourly Sales Analysis
    if hour_plot_type == "Line Chart":
        fig_hourly = px.line(
            sales_by_hour,
            x='hour_12',  # Use the new hour_12 column
            y='total_sales',
            title='Total Sales by Hour for ' + selected_store,
            labels={'total_sales': 'Total Sales', 'hour_12': 'Hour'},
            line_shape='linear'
        )

        # Set line color based on selected color scale
        if selected_hour_color in px.colors.sequential.__dict__:
            line_color = px.colors.sequential.__getattribute__(selected_hour_color)[0]
        else:
            line_color = 'green'

        fig_hourly.update_traces(line=dict(color=line_color))

        if show_data_labels_hour:
            fig_hourly.add_scatter(
                x=sales_by_hour['hour_12'],
                y=sales_by_hour['total_sales'],
                mode='text',
                text=sales_by_hour['total_sales'],
                textposition='top center'
            )

    elif hour_plot_type == "Bar Chart":
        fig_hourly = px.bar(
            sales_by_hour,
            x='hour_12', 
            y='total_sales',
            title='Total Sales by Hour for ' + selected_store,
            labels={'total_sales': 'Total Sales', 'hour_12': 'Hour'},
            color='total_sales',
            color_continuous_scale=selected_hour_color
        )

        if show_data_labels_hour:
            fig_hourly.update_traces(texttemplate='%{y:.2f}', textposition='outside')

    # Update x-axis to show all hour labels and set the range
    fig_hourly.update_xaxes(title_text='Hour', tickmode='linear')

    # Make the plot bigger (adjust size)
    fig_hourly.update_layout(
        width=1000, 
        height=450, 
        margin=dict(l=50, r=50, t=80, b=50)
    )

    # Display the plot and DataFrame for Hourly Sales Analysis
    st.plotly_chart(fig_hourly)
    results['charts']['hourly_sales'] = fig_hourly

    results['dataframes']['hourly_sales'] = sales_by_hour
    sales_by_hour_display = sales_by_hour[['hour_12', 'hour_24', 'total_sales', 'total_cost_price','total_quantity', 'total_profit', 'contribution', 'Company Standard', 'variance']]

    # Display the DataFrame with conditional formatting
    st.table(sales_by_hour_display.style.applymap(lambda x: 'color: red' if isinstance(x, str) and x.endswith('%') and float(x[:-1]) < 0 else '', subset=['variance']))
    


    @st.cache_data
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv_hourly = convert_df(sales_by_hour_display)

    st.sidebar.download_button(
            label="Download Hourly Sales Data",
            data=csv_hourly,   
            file_name='hourly_sales.csv',
            mime='text/csv',
        )

    # Create comparison DataFrame with percentages
    comparison_data = sales_by_hour[['hour_12', 'contribution', 'Company Standard']].copy()
    comparison_data.set_index('hour_12', inplace=True)

    # Convert contribution and Company Standard from strings to float for correct plotting
    comparison_data['contribution'] = comparison_data['contribution'].str.replace('%', '').astype(float)
    comparison_data['Company Standard'] = comparison_data['Company Standard'].str.replace('%', '').astype(float)

    # Create an empty figure
    comparison_fig = go.Figure()

    # Add the contribution trace
    comparison_fig.add_trace(go.Scatter(
        x=comparison_data.index,
        y=comparison_data['contribution'],
        mode='lines+markers',
        name='Contribution',
        line=dict(color='blue')
    ))

    # Add the company standard trace
    comparison_fig.add_trace(go.Scatter(
        x=comparison_data.index,
        y=comparison_data['Company Standard'],
        mode='lines+markers',
        name='Company Standard',
        line=dict(color='green')
    ))

    # Set title and axes labels
    comparison_fig.update_layout(
        title='Comparison of Contribution vs Company Standard',
        xaxis_title='Hour',
        yaxis_title='Percentage (%)',
        yaxis=dict(range=[0, 40]),
        width=1000,
        height=500,
        margin=dict(l=50, r=50, t=80, b=50)
    )

    # Display data labels if selected
    if show_data_labels_hour:
        comparison_fig.for_each_trace(lambda t: t.update(text=t.y, textposition='top center'))

    st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: green; text-align: center;'>Store Sales Contribution VS Company Standard</h4>", unsafe_allow_html=True)
    # Show the plot
    st.plotly_chart(comparison_fig)
    results['charts']['comparison'] = comparison_fig



    sales_over_time = store_data_filtered.groupby('orderDate').agg(
        total_sales=('totalProductPrice', 'sum'),
        total_cost_price=('costPrice', lambda x: (x * store_data_filtered.loc[x.index, 'quantity']).sum()),
        total_quantity=('quantity', 'sum'),
    ).reset_index()

    sales_over_time['total_profit'] = sales_over_time['total_sales'] - sales_over_time['total_cost_price']

    # Calculate total values for percentage contribution
    total_sales_sum = sales_over_time['total_sales'].sum()
    total_cost_price_sum = sales_over_time['total_cost_price'].sum()
    total_quantity_sum = sales_over_time['total_quantity'].sum()

    # Contribution percentage of each day's sales to the total sales of the selected store
    sales_over_time['contribution'] = (sales_over_time['total_sales'] / total_sales_sum) * 100


    all_data['orderDate'] = pd.to_datetime(all_data['orderDate'], errors='coerce')
    daily_sales_all_data = all_data.groupby('orderDate').agg(
        total_sales_all=('totalProductPrice', 'sum')
    ).reset_index()

    sales_over_time = sales_over_time.merge(daily_sales_all_data, on='orderDate', suffixes=('', '_all'), how='left')

    # Now calculate contribution to the entire dataset (all_data)
    total_sales_all_data = all_data['totalProductPrice'].sum()
    sales_over_time['Company Standard'] = (sales_over_time['total_sales_all'] / total_sales_all_data) * 100

    # Sort the data based on the selected order for the plot
    if sort_order == "Descending":
        sales_over_time_sorted = sales_over_time.sort_values(by='total_sales', ascending=False)
    else:
        sales_over_time_sorted = sales_over_time.sort_values(by='total_sales', ascending=True)
   # Create the plot based on the selected type for Time Slot Analysis
    if time_plot_type == "Line Chart":
        fig_time = px.line(
            sales_over_time_sorted,
            x='orderDate',
            y='total_sales',
            title='Daily Sales',
            labels={'total_sales': 'Total Sales', 'orderDate': 'Order Date'},
            line_shape='linear'
        )

        # Set line color based on selected color scale
        if selected_color_time in px.colors.sequential.__dict__:
            line_color = px.colors.sequential.__getattribute__(selected_color_time)[0]
        else:
            line_color = 'blue'

        fig_time.update_traces(line=dict(color=line_color))

        if show_data_labels_time:
            fig_time.add_scatter(
                x=sales_over_time_sorted['orderDate'],
                y=sales_over_time_sorted['total_sales'],
                mode='text',
                text=sales_over_time_sorted['total_sales'].round(2),
                textposition='top center'
            )

    elif time_plot_type == "Bar Chart":
        fig_time = px.bar(
            sales_over_time_sorted,
            x='orderDate',
            y='total_sales',
            title='Daily Sales',
            labels={'total_sales': 'Total Sales', 'orderDate': 'Order Date'},
            color='total_sales', 
            color_continuous_scale=selected_color_time
        )

        if show_data_labels_time:
            fig_time.update_traces(texttemplate='%{y:.2f}', textposition='outside')

    # Update x-axis to show all date labels
    fig_time.update_xaxes(
        title_text='Order Date',
        tickmode='array',
        tickvals=sales_over_time_sorted['orderDate'],
        ticktext=sales_over_time_sorted['orderDate'].dt.strftime('%Y-%m-%d'),
        tickangle=45
    )

    # Increase plot size
    fig_time.update_layout(
        width=1000,
        height=500,
    )

    # Calculation is done above for daily sales analysis, this is just the visualization
    # st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: green; text-align: center;'>Daily Sales</h4>", unsafe_allow_html=True)
    st.markdown("---")
    # Display the plot and DataFrame for Time Slot Analysis
    st.plotly_chart(fig_time)
    results['charts']['daily_sales'] = fig_time
    results['dataframes']['daily_sales'] = sales_over_time_sorted

    # Calculate average daily sales across all data
    average_daily_sales_all = 42358

    # Calculate average daily sales for the selected store
    average_daily_sales_selected_store = sales_over_time['total_sales'].mean()

    # Calculate the variance
    variance = average_daily_sales_selected_store - average_daily_sales_all

    # Prepare display values with comma for thousands
    average_daily_sales_all_display = f"₹{average_daily_sales_all:,.2f}"
    average_daily_sales_selected_store_display = f"₹{average_daily_sales_selected_store:,.2f}"
    variance_display = f"₹{variance:,.2f}"

    # Set color for variance display (green for positive, red for negative)
    variance_color = "red" if variance < 0 else "green"

    # Create equal-width columns
    col1, col2 = st.columns([1, 1])

    # Display Company Standard Average Daily Sales
    with col1:
        st.markdown("<h5 style='text-align: center;'>All Store Average Daily Sales</h5>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center;'>{average_daily_sales_all_display}</h3>", unsafe_allow_html=True)

    # Display Selected Store Average Daily Sales with variance
    with col2:
        st.markdown("<h5 style='text-align: center;'>Selected Store Average Daily Sales</h5>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center;'>{average_daily_sales_selected_store_display}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h6 style='color:{variance_color}; text-align: center;'>Variance: {variance_display}</h6>", unsafe_allow_html=True)


    
    # Format the DataFrame to include percentage symbols
    sales_over_time_sorted['contribution'] = sales_over_time_sorted['contribution'].round(2).astype(str) + '%'
    sales_over_time_sorted['Company Standard'] = sales_over_time_sorted['Company Standard'].round(2).astype(str) + '%'

    # Convert percentage strings back to floats for variance calculation
    sales_over_time_sorted['contribution_float'] = sales_over_time_sorted['contribution'].str.replace('%', '').astype(float) / 100
    sales_over_time_sorted['Company Standard_float'] = sales_over_time_sorted['Company Standard'].str.replace('%', '').astype(float) / 100

    # Calculate variance using the float columns
    sales_over_time_sorted['difference'] = sales_over_time_sorted['contribution_float'] - sales_over_time_sorted['Company Standard_float']

    # Format the variance to include percentage symbol
    sales_over_time_sorted['difference'] = (sales_over_time_sorted['difference'] * 100).round(2).astype(str) + '%'

        # Apply conditional formatting for variance
    def highlight_negative(val):
        # Check if the value is a string and convert it to float for comparison
        if isinstance(val, str) and '%' in val:
            return 'color: red' if float(val.replace('%', '')) < 0 else 'color: black'
        else:
            return 'color: black'

        # Drop the unwanted columns before displaying
    sales_display = sales_over_time_sorted.drop(columns=['contribution_float', 'Company Standard_float', 'total_sales_all'])

    sales_display['total_sales'] = sales_display['total_sales'].apply(lambda x: f"{x:.2f}")
    sales_display['total_cost_price'] = sales_display['total_cost_price'].apply(lambda x: f"{x:.2f}")
    sales_display['total_profit'] = sales_display['total_profit'].apply(lambda x: f"{x:.2f}")

    st.table(sales_display.drop(columns = ['Company Standard', 'difference']))


    csv_daily = convert_df(sales_over_time_sorted.drop(columns=["contribution_float", "Company Standard_float", "total_sales_all"]))

    st.sidebar.download_button(
            label="Download Daily Sales Data",
            data=csv_daily,   
            file_name='daily_sales.csv',
            mime='text/csv',
        )
    # Calculate and display total sums for sales, cost price, quantity, and profit
    total_profit_sum = sales_over_time['total_profit'].sum()

    results['kpis']['daily_sales'] = {
        'total_sales': total_sales_sum,
        'total_quantity': total_quantity_sum,
        'total_cost_price': total_cost_price_sum,
        'total_profit': total_profit_sum
    }

        # Comment or recommendation box with pre-typed recommendations
    st.markdown("<h4 style='color: green; text-align: center; margin-top: 0px;'>Recommendations</h4>", unsafe_allow_html=True)

        # Default recommendations
    default_recommendations = (
            "- Come up with different promotional ideas for the store to draw more audience.\n"
            "- Customer engagement activities during the daytime.\n"
            "- Offers during certain hours of the day in which sales are lacking.\n"
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
            key="recommendations_input_day",
            placeholder="Write your recommendations here...",
            label_visibility="visible",
            help="Write your suggestions or adjustments related to sales categories."
        )

        # Wrap the text area with a custom class for applying styles
    st.markdown('<div class="recommendations-textarea"></div>', unsafe_allow_html=True)


    st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
    # ---- Weekly Sales Analysis ----
    st.markdown("<h4 style='color: green; text-align: center;'>WEEKLY SALES ANALYSIS</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # Add a new column for the day of the week
    store_data_filtered['day_of_week'] = store_data_filtered['orderDate'].dt.day_name()

    weekly_sales = store_data_filtered.groupby('day_of_week').agg(
        total_sales=('totalProductPrice', 'sum'),
        total_cost_price=('costPrice', lambda x: (x * store_data_filtered.loc[x.index, 'quantity']).sum()),
        total_quantity=('quantity', 'sum'),
    ).reset_index()

    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_sales['day_of_week'] = pd.Categorical(weekly_sales['day_of_week'], categories=days_order, ordered=True)
    weekly_sales_sorted = weekly_sales.sort_values('day_of_week')

    weekly_sales_sorted['total_profit'] = weekly_sales_sorted['total_sales'] - weekly_sales_sorted['total_cost_price']

    total_store_sales = weekly_sales_sorted['total_sales'].sum()
    weekly_sales_sorted['sales_contribution'] = (weekly_sales_sorted['total_sales'] / total_store_sales) * 100

    display_df = weekly_sales_sorted.copy()


    display_df['sales_contribution'] = display_df['sales_contribution'].round(2).astype(str) + '%'
    display_df['total_sales'] = display_df['total_sales'].apply(lambda x: f"₹{x:,.2f}")
    display_df['total_cost_price'] = display_df['total_cost_price'].apply(lambda x: f"₹{x:,.2f}")
    display_df['total_profit'] = display_df['total_profit'].apply(lambda x: f"₹{x:,.2f}")
    display_df['total_quantity'] = display_df['total_quantity'].astype(int)


    # Check if the weekly_sales_sorted DataFrame is empty
    if weekly_sales_sorted.empty:
        st.warning("No sales data available for the selected store in this week.")
        return results

    # Sidebar inputs
    st.sidebar.markdown("### Weekly Sales Analysis Settings")

    # User input for plot type for Weekly Sales Analysis (Pie Chart as default)
    week_plot_type = st.sidebar.selectbox(
        "Select Plot Type for Weekly Sales Analysis:",
        ["Pie Chart", "Bar Chart", "Line Chart"],
        key="week_plot_type")

    # User input for color selection for weekly plots
    selected_week_color = st.sidebar.selectbox("Select Color Scale for Weekly Plot:", color_options_time, key="week_color_scale")

    # User input to toggle data labels for Weekly Sales Analysis
    show_data_labels_week = st.sidebar.checkbox("Show Data Labels for Weekly Sales Analysis", value=True, key="show_data_labels_week")


    # Create the plot based on the selected type for Weekly Sales Analysis
    if week_plot_type == "Pie Chart":
        fig_weekly = px.pie(
            weekly_sales_sorted,
            names='day_of_week',
            values='total_sales',
            title='Total Sales by Day of the Week for ' + selected_store,
            hole=0.4 
        )

        # Add data labels if checkbox is checked
        if show_data_labels_week:
            fig_weekly.update_traces(
                textinfo='label+percent+value',
                textposition='outside',
                hoverinfo='label+percent+value'
            )
        else:
            fig_weekly.update_traces(textinfo='none')

    elif week_plot_type == "Bar Chart":
        fig_weekly = px.bar(
            weekly_sales_sorted,  # Use the unformatted DataFrame
            x='day_of_week',
            y='total_sales',
            title='Total Sales by Day of the Week for ' + selected_store,
            labels={'total_sales': 'Total Sales', 'day_of_week': 'Day of the Week'},
            color='total_sales',
            color_continuous_scale=selected_week_color 
        )
        if show_data_labels_week:
            fig_weekly.update_traces(texttemplate='%{y:.2f}', textposition='outside')

    elif week_plot_type == "Line Chart":
        fig_weekly = px.line(
            weekly_sales_sorted,  # Use the unformatted DataFrame
            x='day_of_week',
            y='total_sales',
            title='Total Sales by Day of the Week for ' + selected_store,
            labels={'total_sales': 'Total Sales', 'day_of_week': 'Day of the Week'},
            line_shape='linear'
        )
        
        if show_data_labels_week:
            fig_weekly.add_scatter(
                x=weekly_sales_sorted['day_of_week'],
                y=weekly_sales_sorted['total_sales'],
                mode='text',
                text=weekly_sales_sorted['total_sales'].round(2),
                textposition='top center'
            )

    fig_weekly.update_layout(
        width=1100,
        height=550
    )

    # Display the plot with the updated layout size
    st.plotly_chart(fig_weekly)
    results['charts']['weekly_sales'] = fig_weekly

    # Format percentage contribution with the '%' symbol and round to 2 decimal places
    weekly_sales_sorted['sales_contribution'] = weekly_sales_sorted['sales_contribution'].apply(lambda x: f"{x:.2f}%")
    weekly_sales_sorted['total_sales'] = weekly_sales_sorted['total_sales'].apply(lambda x: f"{x:,.2f}")
    weekly_sales_sorted['total_cost_price'] = weekly_sales_sorted['total_cost_price'].apply(lambda x: f"{x:,.2f}")
    weekly_sales_sorted['total_profit'] = weekly_sales_sorted['total_profit'].apply(lambda x: f"{x:,.2f}")


    # Display the updated DataFrame with percentage change and percentage symbol
    st.table(weekly_sales_sorted)
    results['dataframes']['weekly_sales'] = weekly_sales_sorted

    csv_weekly = convert_df(weekly_sales_sorted)


    st.sidebar.download_button(
            label="Download weekly Data",
            data=csv_weekly,   
            file_name='weekly_sales.csv',
            mime='text/csv',
        )



    return results