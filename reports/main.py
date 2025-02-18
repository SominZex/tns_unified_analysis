import streamlit as st
import pandas as pd
from reports.analysis.sales_by_category import sales_by_category_analysis
from reports.analysis.time_slot_analysis import time_slot_analysis
from reports.analysis.sales_per_channel import sales_per_channel_analysis
from reports.analysis.top_n_brand_sales import top_n_brand_sales_analysis
# from brand_availability import top_n_brand_availability_analysis
from reports.analysis.top_n_products import top_n_product_analysis
# from top_n_product_availability import top_n_product_availability_analysis
from reports.analysis.fnb_performance import fnb_performance_analysis
from reports.analysis.monetized_brands import analyze_monetized_brands
from reports.analysis.counter_shelf_analysis import analyze_counter_shelf_products
# from low_performing_brand import low_performing_brand_analysis
# from low_performing_products import low_performing_product_analysis
from reports.analysis.profit import display_profit_metrics
from reports.analysis.grn_analysis import grn_analysis, upload_stock_data
from reports.analysis.order_analysis import order_analysis
from utils.data_loader import load_data_from_directory, parse_time_dynamic
from PIL import Image
import numpy as np

st.markdown("""
    <style>
    /* General web layout */
    .stApp {
        width: 100%;
        max-width: 1000px; /* Limit the maximum width for better appearance */
        margin: 0 auto; /* Center horizontally */
        padding: 2px; /* Padding for better visuals */
        background-color: white;
        box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
    }

    /* Center the page title */
    h1 {
        text-align: center;
        color: #2e7d32; /* Dark green color */
    }

    /* Style the metrics and other boxed elements */
    .metrics-box {
        border: 1px solid #ccc;
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
        background-color: #f0f4f8;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }

    /* Strong emphasis text style */
    .metrics-box p {
        font-family: 'Arial', sans-serif;
        font-size: 16px;
        line-height: 1.5;
        margin: 5px 0;
    }

    /* Style for RAG analysis (Red, Amber, Green) */
    .rag-red {
        background-color: red;
        color: white;
        font-weight: bold;
        padding: 5px;
        border-radius: 5px;
    }

    .rag-amber {
        background-color: orange;
        color: white;
        font-weight: bold;
        padding: 5px;
        border-radius: 5px;
    }

    .rag-green {
        background-color: green;
        color: white;
        font-weight: bold;
        padding: 5px;
        border-radius: 5px;
    }

    /* A4-specific styling for printing */
    @media print {
        @page {
            size: A4; /* A4 size page */
            margin: 4mm; /* Adjust as needed for print */
        }

        body {
            width: 210mm;  /* A4 width */
            height: 297mm; /* A4 height */
            margin: 0 auto;
            -webkit-print-color-adjust: exact !important; /* Ensure colors are printed accurately */
            color-adjust: exact !important;
        }

        /* Constrain the app to A4 width in print view */
        .stApp {
            max-width: 210mm; /* Limit to A4 width */
            margin: 0 auto; /* Center content on the page */
            padding: 10mm; /* Ensure proper padding for print */
        }

        .metrics-box {
            page-break-inside: avoid;
        }

        /* RAG color preservation during print */
        .rag-red {
            background-color: red !important;
            color: white !important;
        }

        .rag-amber {
            background-color: orange !important;
            color: white !important;
        }

        .rag-green {
            background-color: green !important;
            color: white !important;
        }

        /* Hide unnecessary elements for printing */
        .back-to-top {
            display: none !important;
        }
        
            .back-to-top {
            position: fixed;
            bottom: 20px; /* Position from the bottom */
            right: 20px; /* Position from the right */
            background-color: #2e7d32; /* Dark green color */
            color: white; /* Text color */
            border: none;
            border-radius: 5px;
            padding: 10px;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            display: none; /* Hidden by default */
        }

        /* Show the button when scrolling down */
        body.scroll .back-to-top {
            display: block;
        }

    </style>
""", unsafe_allow_html=True)


#stpdf.init()

# Title
# st.markdown("<h1>🏭 TNS Data Factory (WIP)</h1>", unsafe_allow_html=True)

# Use cache to store uploaded data
@st.cache_data
def load_data(uploaded_file):
    data = pd.read_csv(uploaded_file)

    # Try parsing 'orderDate' explicitly in multiple formats
    date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']
    
    for fmt in date_formats:
        try:
            data['orderDate'] = pd.to_datetime(data['orderDate'], format=fmt, errors='raise')
            break  # Stop if parsing is successful
        except ValueError:
            continue
    
    # If all formats fail, fall back to automatic parsing
    if not pd.api.types.is_datetime64_any_dtype(data['orderDate']):
        data['orderDate'] = pd.to_datetime(data['orderDate'], dayfirst=True, errors='coerce')

    return data

def parse_time(time_str):
    """
    Parse time string in various formats to datetime.time object
    """
    try:
        return pd.to_datetime(time_str, format='%H:%M:%S.%fZ').time()
    except ValueError:
        try:
            return pd.to_datetime(time_str, format='%H:%M:%S').time()
        except ValueError:
            try:
                return pd.to_datetime(time_str, format='%H:%M').time()
            except ValueError:
                return None

if 'data' not in st.session_state:
    st.session_state.data = None
if 'show_uploader' not in st.session_state:
    st.session_state.show_uploader = True

# File uploader
if st.session_state.show_uploader:
    uploaded_file = st.file_uploader("Upload CSV file", type="csv")
    if uploaded_file is not None:
        # Load the uploaded data
        st.session_state.data = pd.read_csv(uploaded_file)
        
        # Parse the 'orderDate' column
        if 'orderDate' in st.session_state.data.columns:
            st.session_state.data['orderDate'] = pd.to_datetime(st.session_state.data['orderDate'], format="mixed", dayfirst=True, errors="coerce")

        # Parse the 'time' column with the new dynamic parsing
        if 'time' in st.session_state.data.columns:
            st.session_state.data['time'] = st.session_state.data['time'].apply(parse_time)
        
        st.session_state.show_uploader = False

# Toggle button to show/hide the uploader
if st.button("^"):
    st.session_state.show_uploader = not st.session_state.show_uploader

# Proceed only if data is loaded
if st.session_state.data is not None:
    data = st.session_state.data

    # Move selectors and inputs to sidebar
    with st.sidebar:
        st.markdown("### Control Panel")
        
        # Store selection
        store_names = data['storeName'].unique()
        selected_store = st.selectbox("Select a Store:", store_names, key="store_selector")

        # Date range selection
        start_date = st.date_input("Select Start Date:", value=data['orderDate'].min().date(),
                                   min_value=data['orderDate'].min().date(),
                                   max_value=data['orderDate'].max().date())
        end_date = st.date_input("Select End Date:", value=data['orderDate'].max().date(),
                                 min_value=data['orderDate'].min().date(),
                                 max_value=data['orderDate'].max().date())

  
    # Convert start_date and end_date to datetime64[ns] for comparison
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    date_range_length = (end_date - start_date).days + 1

    # Filter data based on selected store and date range
    store_data = data[(data['storeName'] == selected_store) & 
                      (data['orderDate'] >= start_date) & 
                      (data['orderDate'] <= end_date)]

    # Filter for available stock using the quantity column
    store_data_filtered = store_data[store_data['quantity'] > 0]

    # Calculate the total number of unique stores for overall data
    overall_unique_store_count = data['storeName'].nunique()

    # Define the performance rating function based on the logic you provided
    def performance_rating(avg_price, overall_average):
        if avg_price > overall_average * 1.2:
            return 'Excellent'
        elif avg_price > overall_average:
            return 'Good'
        elif avg_price == overall_average:
            return 'Average'
        elif avg_price >= overall_average * 0.8:
            return 'Below Average'
        else:
            return 'Poor'
      
    selected_store_total_revenue = store_data['totalProductPrice'].sum()

    overall_data_filtered = data[(data['orderDate'] >= start_date) & 
                              (data['orderDate'] <= end_date)]

    # Calculate total revenue for all stores
    overall_total_revenue = overall_data_filtered['totalProductPrice'].sum()

    if len(overall_data_filtered) > 0:
        overall_avg_sales = 42358 * date_range_length
    else:
        overall_avg_sales = 0

    if len(store_data) > 0:
        selected_store_avg_sales = selected_store_total_revenue / len(store_data)
    else:
        selected_store_avg_sales = 0


    # Calculate the percentage difference from the overall average
    avg_difference_percentage = ((selected_store_avg_sales - overall_avg_sales) / overall_avg_sales) * 100 if overall_avg_sales > 0 else 0

    # Create a DataFrame for store performance
    store_performance = pd.DataFrame({
        'storeName': [selected_store],
        'averageTotalProductPrice': [selected_store_avg_sales],
        'totalRevenue': [selected_store_total_revenue],
        'percentageDifference': [avg_difference_percentage],
        'overallAverage': [overall_avg_sales],
        'overallRevenue': [overall_total_revenue]
    })

    if overall_total_revenue > 0:
        selected_store_percentage_contribution = (selected_store_total_revenue / overall_total_revenue) * 100
    else:
        selected_store_percentage_contribution = 0

    store_performance['performanceRating'] = store_performance['averageTotalProductPrice'].apply(performance_rating, overall_average=overall_avg_sales)
    # Create KPI Cards for key metrics
    st.markdown(f"<h2 style='color: green; text-align: center;'>{selected_store}</h2>", unsafe_allow_html=True)
    st.markdown(
        f"<h4 style='color: green; text-align: center;'>{start_date.date()} to {end_date.date()}</h4>",
        unsafe_allow_html=True
    )
    # Function to display metrics with conditional formatting
    def display_metric(column, label, value, percentage_difference):
        column.metric(label, value)
        # Conditional formatting for delta text
        if percentage_difference > 0:
            delta_text = f'<span style="color: green;">+{percentage_difference:.2f}%</span>'
        elif percentage_difference < 0:
            delta_text = f'<span style="color: red;">{percentage_difference:.2f}%</span>'
        else:
            delta_text = f'<span style="color: grey;">{percentage_difference:.2f}%</span>'
        column.markdown(delta_text, unsafe_allow_html=True)

    # Calculate the percentage difference between overall average sales and store total revenue
    total_revenue_difference_percentage = ((selected_store_total_revenue - overall_avg_sales) / overall_avg_sales) * 100

    # Create three equal columns
    col1, col2, col3 = st.columns(3, gap="large")

    # Custom CSS for perfect alignment and conditional formatting
    custom_metric_style = """
        <style>
            [data-testid="metric-container"] {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                margin: 0 auto;
                padding: 0;
            }
            [data-testid="stMetricValue"] {
                display: flex;
                justify-content: center;
                align-items: left;
            }
            [data-testid="stMetricLabel"] {
                display: flex;
                justify-content: center;
                align-items: left;
            }
            .negative {
                color: rgb(255, 43, 43) !important;
            }
            .positive {
                color: rgb(9, 171, 59) !important;
            }
        </style>
    """
    st.markdown(custom_metric_style, unsafe_allow_html=True)

    # Store Revenue in col1
    with col1:
        st.metric(
            "Store Revenue",
            f"₹{store_performance['totalRevenue'].values[0]:,.2f}"
        )

    # Overall Average Sales in col2
    with col2:
        st.metric(
            "Overall Average Sales",
            f"₹{overall_avg_sales:,.2f}"
        )

    # Revenue Difference Percentage in col3 with conditional formatting
    with col3:
        st.metric(
            label="Difference",
            value=f"{total_revenue_difference_percentage:.2f}%",
            delta=f"{total_revenue_difference_percentage:+.2f}%",
            delta_color="normal"  
        )

    display_profit_metrics(data, selected_store, start_date, end_date)
    order_analysis(store_data)
    selected_store_data = data[data['storeName'] == selected_store]
    all_data = data.copy()
    sales_by_category_analysis(store_data, all_data)
    time_slot_analysis(store_data, all_data)

    selected_store_data = data[data['storeName'] == selected_store]
    selected_store_data['orderDate'] = pd.to_datetime(selected_store_data['orderDate'], format='%d-%m-%Y')
    
    selected_store_data['year'] = selected_store_data['orderDate'].dt.isocalendar().year
    selected_store_data['week'] = selected_store_data['orderDate'].dt.isocalendar().week
    selected_store_data['year'] = selected_store_data['orderDate'].dt.year
    selected_store_data['month'] = selected_store_data['orderDate'].dt.month

    filtered_data = data[(data['orderDate'] >= start_date) & (data['orderDate'] <= end_date)]

    filtered_data['month'] = filtered_data['orderDate'].dt.month

    # Calculate monthly sales for each store
    monthly_sales_per_store = filtered_data.groupby(['storeName', 'month'])['totalProductPrice'].sum().reset_index()

    # Calculate average monthly sales for each store
    average_monthly_sales_per_store = monthly_sales_per_store.groupby('storeName')['totalProductPrice'].mean().reset_index()
    average_monthly_sales_per_store.rename(columns={'totalProductPrice': 'averageMonthlySales'}, inplace=True)

    # Calculate overall average monthly sales based on unique store names in the filtered data
    overall_average_monthly_sales = filtered_data['totalProductPrice'].sum() / filtered_data['month'].nunique() / filtered_data['storeName'].nunique()

    # Calculate percentage difference
    average_monthly_sales_per_store['percentageDifference'] = (
        (average_monthly_sales_per_store['averageMonthlySales'] - overall_average_monthly_sales) / overall_average_monthly_sales
    ) * 100

        # Add overall average to the DataFrame
    average_monthly_sales_per_store['overallAverageMonthlySales'] = overall_average_monthly_sales

    data['orderDate'] = pd.to_datetime(data['orderDate'], format='%d-%m-%Y', errors='coerce')

    # Filter data for the selected date range
    filtered_data = data[(data['orderDate'] >= start_date) & (data['orderDate'] <= end_date)]

    # Calculate daily sales for each store
    daily_sales_per_store = filtered_data.groupby(['storeName', 'orderDate'])['totalProductPrice'].sum().reset_index()

    # Calculate average daily sales for each store
    average_daily_sales_per_store = daily_sales_per_store.groupby('storeName')['totalProductPrice'].mean().reset_index()
    average_daily_sales_per_store.rename(columns={'totalProductPrice': 'averageDailySales'}, inplace=True)

    # Calculate overall average daily sales based on unique store names in the filtered data
    overall_average_daily_sales = filtered_data['totalProductPrice'].sum() / filtered_data['orderDate'].nunique() / filtered_data['storeName'].nunique()

    # Calculate percentage difference
    average_daily_sales_per_store['percentageDifference'] = (
        (average_daily_sales_per_store['averageDailySales'] - overall_average_daily_sales) / overall_average_daily_sales
    ) * 100

    # Add overall average daily sales to the DataFrame
    average_daily_sales_per_store['overallAverageDailySales'] = overall_average_daily_sales

    # Convert 'orderDate' to datetime
    data['orderDate'] = pd.to_datetime(data['orderDate'], format='%d-%m-%Y', errors='coerce')

    # Filter data for the selected date range
    filtered_data = data[(data['orderDate'] >= start_date) & (data['orderDate'] <= end_date)]

    # Extract week number from orderDate
    filtered_data['week_number'] = filtered_data['orderDate'].dt.isocalendar().week

    weekly_sales_per_store = filtered_data.groupby(['storeName', 'week_number'])['totalProductPrice'].sum().reset_index()

    average_weekly_sales_per_store = weekly_sales_per_store.groupby('storeName')['totalProductPrice'].mean().reset_index()
    average_weekly_sales_per_store.rename(columns={'totalProductPrice': 'averageWeeklySales'}, inplace=True)

    overall_average_weekly_sales = filtered_data['totalProductPrice'].sum() / filtered_data['week_number'].nunique() / filtered_data['storeName'].nunique()

    average_weekly_sales_per_store['percentageDifference'] = (
        (average_weekly_sales_per_store['averageWeeklySales'] - overall_average_weekly_sales) / overall_average_weekly_sales
    ) * 100

    average_weekly_sales_per_store['overallAverageWeeklySales'] = overall_average_weekly_sales

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown(
            f"""
            <div style='background-color: #f0f0f0; border: 2px solid #0072B8; border-radius: 10px; padding: 8px; width: 250px; margin: auto;'> 

            <h1 style='text-align: center; margin: 0; font-size: 26px;'>Daily:</h1>
            <hr style='border: 1px solid #0072B8; width: 80%; margin: auto;'/>

            <h4 style='text-align: center; margin: 0; font-size: 14px;'>Store Avg. Daily Sales</h4>
            <h3 style='text-align: center; margin: 5px 0; font-size: 24px;'>₹ {average_daily_sales_per_store[average_daily_sales_per_store['storeName'] == selected_store]['averageDailySales'].mean():,.2f}</h3>

            <h4 style='text-align: center; margin: 0; font-size: 14px;'>Overall Avg.</h4>
            <h3 style='text-align: center; margin: 5px 0; font-size: 24px;'>₹ {42358:,.2f}</h3>
            """,
            unsafe_allow_html=True
        )

        store_avg = average_daily_sales_per_store[average_daily_sales_per_store['storeName'] == selected_store]['averageDailySales'].mean()
        percentage_difference_daily = ((store_avg - 42358) / 42358) * 100

        if percentage_difference_daily > 0:
            st.markdown(f"<h4 style='color: green; text-align: center; margin: 0; font-size: 16px;'>+{percentage_difference_daily:.2f}%</h4>", unsafe_allow_html=True)
        elif percentage_difference_daily < 0:
            st.markdown(f"<h4 style='color: red; text-align: center; margin: 0; font-size: 16px;'>{percentage_difference_daily:.2f}%</h4>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h4 style='color: orange; text-align: center; margin: 0; font-size: 16px;'>No Change</h4>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        if filtered_data.empty:
            st.markdown("<h4 style='text-align: center; color: red;'>No data available for the selected store and date range.</h4>", unsafe_allow_html=True)

    with col2:
        st.markdown(
            f"""
            <div style='background-color: #f0f0f0; border: 2px solid #0072B8; border-radius: 10px; padding: 8px; width: 250px; margin: auto;'> 

            <h1 style='text-align: center; margin: 0; font-size: 26px;'>Weekly:</h1>
            <hr style='border: 1px solid #0072B8; width: 80%; margin: auto;'/>

            <h4 style='text-align: center; margin: 0; font-size: 14px;'>Store Avg. Weekly Sales</h4>
            <h3 style='text-align: center; margin: 5px 0; font-size: 24px;'>₹ {average_weekly_sales_per_store[average_weekly_sales_per_store['storeName'] == selected_store]['averageWeeklySales'].mean():,.2f}</h3>

            <h4 style='text-align: center; margin: 0; font-size: 14px;'>Overall Avg.</h4>
            <h3 style='text-align: center; margin: 5px 0; font-size: 24px;'>₹ {42358 * 7:,.2f}</h3>
            """,
            unsafe_allow_html=True
        )


        store_avg_weekly = average_weekly_sales_per_store[average_weekly_sales_per_store['storeName'] == selected_store]['averageWeeklySales'].mean()
        overall_avg_weekly = 42358 * 7
        percentage_difference_weekly = ((store_avg_weekly - overall_avg_weekly) / overall_avg_weekly) * 100

        if percentage_difference_weekly > 0:
            st.markdown(f"<h4 style='color: green; text-align: center; margin: 0; font-size: 16px;'>+{percentage_difference_weekly:.2f}%</h4>", unsafe_allow_html=True)
        elif percentage_difference_weekly < 0:
            st.markdown(f"<h4 style='color: red; text-align: center; margin: 0; font-size: 16px;'>{percentage_difference_weekly:.2f}%</h4>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h4 style='color: orange; text-align: center; margin: 0; font-size: 16px;'>No Change</h4>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Display a message if no data is available for the selected store and date range
    if filtered_data.empty:
        st.markdown("<h4 style='text-align: center; color: red;'>No data available for the selected store and date range.</h4>", unsafe_allow_html=True)


    with col3: 
        st.markdown(
            f"""
            <div style='background-color: #f0f0f0; border: 2px solid #0072B8; border-radius: 10px; padding: 8px; width: 250px; margin: auto;'> 

            <h1 style='text-align: center; margin: 0; font-size: 26px;'>Monthly:</h1>
            <hr style='border: 1px solid #0072B8; width: 80%; margin: auto;'/>

            <h4 style='text-align: center; margin: 0; font-size: 14px;'>Store Avg. Monthly Sales</h4>
            <h3 style='text-align: center; margin: 5px 0; font-size: 24px;'>₹ {average_monthly_sales_per_store[average_monthly_sales_per_store['storeName'] == selected_store]['averageMonthlySales'].mean():,.2f}</h3>

            <h4 style='text-align: center; margin: 0; font-size: 14px;'>Overall Avg.</h4>
            <h3 style='text-align: center; margin: 5px 0; font-size: 24px;'>₹ {42358 * 30:,.2f}</h3>
            """,
            unsafe_allow_html=True
        )

        store_avg_monthly = average_monthly_sales_per_store[average_monthly_sales_per_store['storeName'] == selected_store]['averageMonthlySales'].mean()
        overall_avg_monthly = 42358 * 30
        percentage_difference_monthly = ((store_avg_monthly - overall_avg_monthly) / overall_avg_monthly) * 100

        if percentage_difference_monthly > 0:
            st.markdown(f"<h4 style='color: green; text-align: center; margin: 0; font-size: 16px;'>+{percentage_difference_monthly:.2f}%</h4>", unsafe_allow_html=True)
        elif percentage_difference_monthly < 0:
            st.markdown(f"<h4 style='color: red; text-align: center; margin: 0; font-size: 16px;'>{percentage_difference_monthly:.2f}%</h4>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h4 style='color: orange; text-align: center; margin: 0; font-size: 16px;'>No Change</h4>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    if filtered_data.empty:
        st.markdown("<h4 style='text-align: center; color: red;'>No data available for the selected store and date range.</h4>", unsafe_allow_html=True)

    sales_per_channel_analysis(store_data, data)
    top_n_brand_df = top_n_brand_sales_analysis(store_data, all_data)
    top_n_product_analysis(store_data, all_data)
    fnb_performance_analysis(store_data, all_data)
    analyze_monetized_brands(store_data, all_data)
    analyze_counter_shelf_products(store_data, all_data)

    with st.sidebar:
        st.markdown("---")
        st.markdown("### Additional Analysis")

        st.markdown("<h4 style='color: green; text-align: center;'>Upload Stock Data</h4>", unsafe_allow_html=True)
        stock_data = upload_stock_data()  

    if stock_data is not None:
        st.markdown("<h4 style='color: green; text-align: center;'>Stock/Inventory Analysis</h4>", unsafe_allow_html=True)
        st.markdown("---")

        grn_analysis(st.session_state.data, stock_data, selected_store)
        st.markdown("<h4 style='color: green; text-align: center; margin-top: 0px;'>Recommendations</h4>", unsafe_allow_html=True)
        feedback = st.text_area("", "", key="feedback_input_grn")

        if feedback:
            st.markdown("###### Submitted Feedback:")
            st.write(feedback)


with st.sidebar:
    st.markdown("### Attach Screenshots")
    uploaded_files = st.file_uploader("Upload screenshots", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

st.markdown("""
    <h2 style='text-align: center; color: #2e7d32;'>Google Reviews</h2>
""", unsafe_allow_html=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file)
        st.image(image, caption="User Review", use_column_width=True)
else:
    st.info("Upload screenshots from the sidebar to display them here.")
