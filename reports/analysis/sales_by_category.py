import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def sales_by_category_analysis(store_data, all_data):
    results = {
        'sales_per_category': None,
        'category_chart': None,
        'store_kpis': None,
        #'weekly_sales': None,
        #'monthly_sales': None
    }

    store_data['totalProductPrice'] = pd.to_numeric(store_data['totalProductPrice'], errors='coerce')
    store_data['quantity'] = pd.to_numeric(store_data['quantity'], errors='coerce')
    store_data['costPrice'] = pd.to_numeric(store_data['costPrice'], errors='coerce')

    st.markdown("<h4 style='color: green; text-align: center; margin-top: 0px;'>💰 SALES BY CATEGORY</h4>", unsafe_allow_html=True)

    # Group by category and calculate necessary metrics for the selected store
    sales_per_category = store_data.groupby('subCategoryOf').agg(
        total_sales=('totalProductPrice', 'sum'),
        total_quantity=('quantity', 'sum'),
        total_cost_price=('costPrice', 'sum'),
    ).reset_index()

    # Calculate profit and profit margin
    sales_per_category['profit'] = sales_per_category['total_sales'] - sales_per_category['total_cost_price']
    sales_per_category['profit_margin'] = (sales_per_category['profit'] / sales_per_category['total_sales']) * 100

    # Sort by total sales
    sales_per_category = sales_per_category.sort_values(by='total_sales', ascending=False)

    # Load company benchmark data
    company_benchmark = pd.read_csv('./reports/company_bechmark/category_benchmark.csv')

    # Merge with company benchmark data
    sales_per_category = sales_per_category.merge(company_benchmark, on='subCategoryOf', how='left')

    # Calculate total sales across all categories
    total_sales = sales_per_category['total_sales'].sum()
    sales_per_category['profit_contribution'] = (sales_per_category['total_sales'] / total_sales) * 100

    #revenue contribution
    sales_per_category['revenue_contribution'] = (sales_per_category['total_sales'] / total_sales) * 100

    # Convert profit_margin and percentage_contribution to string with "%" symbol
    sales_per_category['profit_margin'] = sales_per_category['profit_margin'].apply(lambda x: f"{x:.2f}%")
    sales_per_category['profit_contribution'] = sales_per_category['profit_contribution'].apply(lambda x: f"{x:.2f}%")

    results['sales_per_category'] = sales_per_category

    # Sidebar for user inputs
    with st.sidebar:
        st.markdown("### Sales Category Analysis Options")

        # Ensure that the default value does not exceed the maximum value
        max_categories = len(sales_per_category)
        top_n = st.number_input("Select Top-N categories to display:", min_value=0, max_value=max_categories, value=min(20, max_categories), key="top_n_category")

    top_sales_per_category = sales_per_category.head(top_n)

    total_sales_sum = sales_per_category['total_sales'].sum()
    total_quantity_sum = sales_per_category['total_quantity'].sum()
    total_cost_price_sum = sales_per_category['total_cost_price'].sum()
    total_profit_sum = sales_per_category['profit'].sum()


    sales_per_category['total_sales'] = sales_per_category['total_sales'].round(2)

    # Calculate total sales across all categories
    total_sales = sales_per_category['total_sales'].sum()
 
       # Contribution of each category to the total sales (store level)
    sales_per_category['contribution'] = np.where(total_sales != 0,
        (sales_per_category['total_sales'] / total_sales * 100).round(2), 0)

    # Calculate Variance as the percentage difference between the store contribution and company standard
    sales_per_category['variance'] = ((sales_per_category['contribution'] - sales_per_category['Company Standard']) / sales_per_category['Company Standard']).round(2)

    # Replace empty strings with NaN
    sales_per_category.replace('', np.nan, inplace=True)

    # Ensure numeric types for calculations
    sales_per_category['profit_margin'] = pd.to_numeric(sales_per_category['profit_margin'], errors='coerce')
    sales_per_category['contribution'] = pd.to_numeric(sales_per_category['contribution'], errors='coerce')
    sales_per_category['Company Standard'] = pd.to_numeric(sales_per_category['Company Standard'], errors='coerce')
    sales_per_category['variance'] = pd.to_numeric(sales_per_category['variance'], errors='coerce')

    sales_per_category["difference"] = sales_per_category['contribution'] - sales_per_category['Company Standard']

    # Round the difference to 2 decimal places
    sales_per_category['difference'] = sales_per_category['difference'].round(2)

    # Handle NaN values (example: filling with 0)
    sales_per_category.fillna(0, inplace=True)

    # Convert profit_margin, contribution, Company Standard, and variance to string with "%" symbol
    sales_per_category['profit_margin'] = sales_per_category['profit_margin'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else '')
    sales_per_category['contribution'] = sales_per_category['contribution'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else '')
    sales_per_category['Company Standard'] = sales_per_category['Company Standard'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else '')
    sales_per_category['variance'] = sales_per_category['variance'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else '')
    sales_per_category['difference'] = sales_per_category['difference'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else '')


    # Round total_sales to 2 decimal places for display
    sales_per_category['total_sales'] = sales_per_category['total_sales'].apply(lambda x: f"{x:.2f}")


    # Define a function to highlight negative variances in red
    def highlight_negative_variance(val):
        if pd.isnull(val) or val == '':
            return ''
        color = 'red' if float(val[:-1]) < 0 else ''
        return f'color: {color}'

    def highlight_negative_difference(val):
        if pd.isnull(val) or val == '':
            return ''
        color = 'red' if float(val[:-1]) < 0 else ''  
        return f'color: {color}'



    with st.sidebar:
        st.markdown("### Sales Category Comparison Options")

        # Top-N categories input (reflecting lowest to highest)
        top_n_comparison = st.number_input("Select Top-N categories to display for comparison (lowest to highest):", 
                                        min_value=0, max_value=max_categories, 
                                        value=min(50, max_categories), key="top_n_category_2")

        # Plot type selector
        plot_type_comparison = st.selectbox("Select Plot for 3 Week Average:", ["Line Chart", "Column Chart"], key="plot_type_comparison_1")

        # Toggle data labels
        show_data_labels_comparison = st.checkbox("Show Data Labels", value=True, key="show_data_labels_comparison_1")

    # Select the top-N categories sorted from lowest to highest total sales
    top_sales_per_category_comparison = sales_per_category.head(top_n_comparison)

    # Create the comparison chart (line or column)
    if plot_type_comparison == "Line Chart":
        fig_comparison = go.Figure()

        fig_comparison.add_trace(go.Scatter(
            x=top_sales_per_category_comparison['subCategoryOf'],
            y=top_sales_per_category_comparison['contribution'],
            mode='lines+markers',
            name='Contribution%',
            line=dict(color='blue'),
        ))

        fig_comparison.add_trace(go.Scatter(
            x=top_sales_per_category_comparison['subCategoryOf'],
            y=top_sales_per_category_comparison['Company Standard'],
            mode='lines+markers',
            name='Company Standard',
            line=dict(color='orange'),
        ))

        fig_comparison.update_layout(
            title="Contribution% vs Company Standard",
            xaxis_title="Category",
            yaxis_title="Percentage(%)",
            height=550,
            width=1100,
        )

    elif plot_type_comparison == "Column Chart":
        fig_comparison = go.Figure()

        fig_comparison.add_trace(go.Bar(
            x=top_sales_per_category_comparison['subCategoryOf'],
            y=top_sales_per_category_comparison['contribution'],
            name='Contribution%',
            marker_color='blue',
        ))

        fig_comparison.add_trace(go.Bar(
            x=top_sales_per_category_comparison['subCategoryOf'],
            y=top_sales_per_category_comparison['Company Standard'],
            name='Company Standard',
            marker_color='orange',
        ))

        fig_comparison.update_layout(
            title="Contribution% vs Company Standard",
            xaxis_title="Category",
            yaxis_title="Percentage(%)",
            barmode='group',
            height=550,
            width=1100,
        )

    # labels if toggled
    if show_data_labels_comparison:
        if plot_type_comparison == "Column Chart":
            fig_comparison.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
        else:
            fig_comparison.update_traces(texttemplate='%{y:.2f}%', textposition='top center')

    # Display the comparison chart
    st.plotly_chart(fig_comparison)

    # Custom CSS to center the dataframe in the web app
    custom_css = """
    <style>
        .dataframe-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
        }
        div.stDataFrameContainer {
            width: 1000% !important; 
            margin: 0 auto; 
        }
    </style>
    """

    st.markdown(custom_css, unsafe_allow_html=True)

    with st.container():
        final_df = sales_per_category[['subCategoryOf', 'total_sales', 'contribution', 'Company Standard', 'variance', 'difference']].style.applymap(
            highlight_negative_variance, subset=['variance']).applymap(
            highlight_negative_difference, subset=['difference']).set_table_styles(
            [{
                'selector': 'thead th',
                'props': [('text-align', 'center')]
            }, {
                'selector': 'tbody td',
                'props': [('text-align', 'center')]
            }]
        )

        # Display the DataFrame inside a wrapper to center it
        st.markdown('<div class="dataframe-wrapper">', unsafe_allow_html=True)
        st.table(final_df) 

        # Comment or recommendation box with pre-typed recommendations
        st.markdown("<h4 style='color: green; text-align: center; margin-top: 0px;'>Recommendations</h4>", unsafe_allow_html=True)

        # Default recommendations
        default_recommendations = (
            "- Come up with offers to increase the sales of the above categories.\n"
            "- Also, check the visibility of the same.\n"
            "- Upskill the customer service at the store to increase the sales.\n"
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
            key="recommendations_input",
            placeholder="Write your recommendations here...",
            label_visibility="visible",
            help="Write your suggestions or adjustments related to sales categories."
        )

        # Wrap the text area with a custom class for applying styles
        st.markdown('<div class="recommendations-textarea"></div>', unsafe_allow_html=True)

        # # Display the feedback below the table if provided
        # if feedback:
        #     st.markdown("###### Submitted Feedback:")
        #     st.write(feedback)



    @st.cache_data
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv_cat = convert_df(sales_per_category.drop(columns=['profit_margin']))

    st.sidebar.download_button(
            label="Download Category Sales Data",
            data=csv_cat,   
            file_name='sales_by_category.csv',
            mime='text/csv',
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # Store the results
    results['sales_per_category'] = sales_per_category



    results['store_kpis'] = {
        'total_quantity_sum': total_quantity_sum,
        'total_cost_price_sum': total_cost_price_sum,
        'total_profit_sum': total_profit_sum
    }



    # --- Comparing Weekly Sales by Category ---
    if st.sidebar.checkbox("Show Weekly Sales Comparison on selected categories", value=False):
        st.markdown("---")
        st.markdown(
            """
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
            """,
            unsafe_allow_html=True
        )
        st.markdown("<h2 style='color: green; text-align: center;'><i class='fas fa-calendar-alt'></i> Weekly Sales Comparison by Category</h2>", unsafe_allow_html=True)

        st.markdown("---")

        # Helper function to calculate percentage change
        def calculate_percentage_change(previous, current):
            if previous == 0 and current == 0:
                return 0
            elif previous == 0:
                return 100
            else:
                return ((current - previous) / previous) * 100

        # Select the store dynamically
        selected_store = st.selectbox("Select a Store:", store_data['storeName'].unique(), key="store_selection")

        # Filter store_data for the selected store
        filtered_store_data = store_data[store_data['storeName'] == selected_store]

        # Create week, year, and month columns
        filtered_store_data['week'] = filtered_store_data['orderDate'].dt.isocalendar().week
        filtered_store_data['year'] = filtered_store_data['orderDate'].dt.year
        filtered_store_data['month'] = filtered_store_data['orderDate'].dt.strftime('%b')

        # Create a column to identify week number within the month
        filtered_store_data['week_of_month'] = filtered_store_data['orderDate'].apply(lambda x: (x.day - 1) // 7 + 1)

        # Pivot the DataFrame to create separate columns for each week
        weekly_sales_per_category = filtered_store_data.pivot_table(
            index=['subCategoryOf', 'year', 'month'],
            columns='week_of_month',
            values='totalProductPrice',
            aggfunc='sum'
        ).reset_index()

        # Rename the columns for better readability
        weekly_sales_per_category.columns = ['subCategoryOf', 'year', 'month'] + [f'Week {int(col)}' for col in weekly_sales_per_category.columns[3:]]

        # Fill missing values with 0 (weeks with no sales)
        weekly_sales_per_category.fillna(0, inplace=True)

        # Dynamically determine the number of weeks present
        num_weeks = weekly_sales_per_category.shape[1] - 3

        # Calculate percentage change for weekly sales (week over week)
        for i in range(1, num_weeks):
            current_week = f'Week {i}'
            next_week = f'Week {i+1}'
            change_column = f'{next_week} % Change'
            
            weekly_sales_per_category[change_column] = weekly_sales_per_category.apply(
                lambda row: calculate_percentage_change(row[current_week], row[next_week]),
                axis=1
            )

        # Format the percentage change columns
        for i in range(1, num_weeks):
            change_column = f'Week {i+1} % Change'
            weekly_sales_per_category[change_column] = weekly_sales_per_category[change_column].apply(
                lambda x: f"{x:+.2f}%" if pd.notnull(x) and x != 100 else "N/A" if pd.isnull(x) else "+100%"
            )
            
        # Select a category for weekly sales comparison
        unique_key = f"category_weekly_{selected_store}"
        selected_category = st.selectbox(
            "Select a Category for Weekly Sales Comparison:",
            weekly_sales_per_category['subCategoryOf'].unique(),
            key=unique_key 
        )

        # Filter data for the selected category
        category_weekly_sales = weekly_sales_per_category[weekly_sales_per_category['subCategoryOf'] == selected_category]

        # Show data labels
        show_data_labels = st.checkbox("Show Data Labels", value=st.session_state.get("show_data_labels", True), key="data_labels_checkbox")
        st.session_state.show_data_labels = show_data_labels

        # Create a line plot for weekly sales
        fig_weekly_sales = px.line(
            category_weekly_sales.melt(id_vars=['subCategoryOf', 'year', 'month'], value_vars=[f'Week {i}' for i in range(1, num_weeks + 1)], var_name='Week', value_name='Total Sales'),
            x='Week',
            y='Total Sales',
            title=f'Weekly Sales Trend for {selected_category} in {selected_store}',
            labels={'Total Sales': 'Total Sales', 'Week': 'Week'},
            markers=True,
            text=category_weekly_sales.melt(id_vars=['subCategoryOf', 'year', 'month'], value_vars=[f'Week {i}' for i in range(1, num_weeks + 1)], var_name='Week', value_name='Total Sales')['Total Sales'] if show_data_labels else None
        )

        if show_data_labels:
            fig_weekly_sales.update_traces(textposition='top center')

        # Adjust the layout to make the plot bigger
        fig_weekly_sales.update_layout(
            width=1100,
            height=550
        )

        st.plotly_chart(fig_weekly_sales)

        results['weekly_sales'] = {
            'data': weekly_sales_per_category,
            'chart': fig_weekly_sales
        }
        st.subheader(f"Weekly Sales Data for {selected_store}")
        st.dataframe(weekly_sales_per_category)

        # Comment or recommendation box
        st.markdown("<h4 style='color: green; text-align: center; margin-top: 0px;'>Recommendations</h4>", unsafe_allow_html=True)
        feedback = st.text_area("", "")

        # Display the feedback below the table
        if feedback:
            st.markdown("###### Submitted Feedback:")
            st.write(feedback)

    # --- Monthly Sales Trend ---
    if st.sidebar.checkbox("Show Monthly Sales Trend on selected categories", value=False):
        # Extract month and year
        store_data['month_year'] = store_data['orderDate'].dt.to_period('M')
        
        # Group by category, year, and month
        monthly_sales_per_category = store_data.groupby(['subCategoryOf', 'month_year'])['totalProductPrice'].sum().reset_index()
        
        # Convert month-year to datetime for better plotting
        monthly_sales_per_category['month_year'] = monthly_sales_per_category['month_year'].dt.to_timestamp()

        # Provide plot type options
        plot_type = st.selectbox("Select Plot Type", ["Line Chart", "Bar Chart", "Area Chart"], key="monthly_plot_type")

        # Create plots based on selected plot type
        if plot_type == "Line Chart":
            fig_monthly_sales = px.line(
                monthly_sales_per_category,
                x='month_year',
                y='totalProductPrice',
                color='subCategoryOf',
                title='Monthly Sales Trend by Category (Line Chart)',
                labels={'totalProductPrice': 'Total Sales', 'month_year': 'Month-Year'},
                markers=True
            )
        elif plot_type == "Bar Chart":
            fig_monthly_sales = px.bar(
                monthly_sales_per_category,
                x='month_year',
                y='totalProductPrice',
                color='subCategoryOf',
                title='Monthly Sales Trend by Category (Bar Chart)',
                labels={'totalProductPrice': 'Total Sales', 'month_year': 'Month-Year'}
            )
        elif plot_type == "Area Chart":
            fig_monthly_sales = px.area(
                monthly_sales_per_category,
                x='month_year',
                y='totalProductPrice',
                color='subCategoryOf',
                title='Monthly Sales Trend by Category (Area Chart)',
                labels={'totalProductPrice': 'Total Sales', 'month_year': 'Month-Year'}
            )

        # Enhance the layout for readability and set the plot size
        fig_monthly_sales.update_layout(
            xaxis_title='Month-Year',
            yaxis_title='Total Sales',
            hovermode='x unified',
            width=1100,
            height=550 
        )

        # Display the plot
        st.plotly_chart(fig_monthly_sales)

        results['monthly_sales'] = {
            'data': monthly_sales_per_category,
            'chart': fig_monthly_sales
        }

    # --- Comparing Sales Across Categories ---
    if st.sidebar.checkbox("Compare Category Sales", value=False, key="sales_comparison"):
        selected_categories = st.multiselect("Select Categories to Compare:", sales_per_category['subCategoryOf'].unique(), key="category_compare")
        
        if selected_categories:
            comparison_data = store_data[store_data['subCategoryOf'].isin(selected_categories)]
            comparison_sales = comparison_data.groupby(['subCategoryOf', 'month'])['totalProductPrice'].sum().reset_index()

            # Dropdown to select chart type
            chart_type = st.selectbox("Select Chart Type:", ["Grouped Bar Chart", "Stacked Bar Chart"], key="chart_type")

            # Toggle for data labels with a unique key
            show_data_labels = st.checkbox("Show Data Labels", value=True, key="show_data_labels")

            if chart_type == "Grouped Bar Chart":
                # Create a grouped bar chart
                fig_comparison_sales = px.bar(
                    comparison_sales,
                    x='month',
                    y='totalProductPrice',
                    color='subCategoryOf',
                    barmode='group', 
                    title='Sales Comparison Across Categories by Month',
                    labels={'totalProductPrice': 'Total Sales', 'month': 'Month'},
                    height=400 
                )

                # Add data labels if checkbox is selected
                if show_data_labels:
                    fig_comparison_sales.for_each_trace(lambda t: t.update(text=t.y, textposition='outside'))

                # Enhance layout
                fig_comparison_sales.update_layout(
                    xaxis_title='Month',
                    yaxis_title='Total Sales',
                    legend_title='Category',
                    xaxis=dict(tickvals=comparison_sales['month'].unique())
                )

            elif chart_type == "Stacked Bar Chart":
                # Create a stacked bar chart
                fig_comparison_sales = px.bar(
                    comparison_sales,
                    x='month',
                    y='totalProductPrice',
                    color='subCategoryOf',
                    title='Sales Comparison Across Categories by Month',
                    labels={'totalProductPrice': 'Total Sales', 'month': 'Month'},
                    height=400,
                    barmode='stack'
                )

                # Add data labels if checkbox is selected
                if show_data_labels:
                    fig_comparison_sales.for_each_trace(lambda t: t.update(text=t.y, textposition='inside'))

                # Enhance layout
                fig_comparison_sales.update_layout(
                    xaxis_title='Month',
                    yaxis_title='Total Sales',
                    legend_title='Category',
                    xaxis=dict(tickvals=comparison_sales['month'].unique())
                )

            st.plotly_chart(fig_comparison_sales)

            results['sales_comparison'] = {
                'data': comparison_sales,
                'chart': fig_comparison_sales
            }



    ## Weekly contribution analysis
    # Ensure orderDate is in datetime format
    store_data['orderDate'] = pd.to_datetime(store_data['orderDate'], errors='coerce')

    store_data = store_data.dropna(subset=['orderDate'])


    unique_months = store_data['orderDate'].dt.to_period('M').unique()

    if len(unique_months) == 0:
        st.error("No valid months found in the dataset. Please check your data.")
        return None
    month_options = [month.strftime('%Y-%m') for month in unique_months]

    if not month_options:
        st.error("Unable to extract months from the dataset.")
        return None

    selected_month = st.sidebar.selectbox(
    "Select Month for 3 Week Average Calculation:", 
    month_options, 
    index=len(month_options) - 1,
    key = "category_sales"
    )
    try:
        selected_month_period = pd.to_datetime(selected_month).to_period('M')
        
        # Filter store data by the selected month
        store_data = store_data[store_data['orderDate'].dt.to_period('M') == selected_month_period]
        
        # Proceed with rest of the analysis...
    except Exception as e:
        st.error(f"Error processing selected month: {e}")
        return None 

    selected_month = st.sidebar.selectbox("Select Month for 3 Week Average Calculation:", month_options)

    # Filter store data by the selected month
    selected_month_period = pd.to_datetime(selected_month).to_period('M')
    store_data = store_data[store_data['orderDate'].dt.to_period('M') == selected_month_period]

    # Step 1: Weekly Average Analysis
    store_data['week'] = store_data['orderDate'].dt.isocalendar().week
    store_data['year'] = store_data['orderDate'].dt.year

    # Group by week and category to calculate total sales
    weekly_sales = store_data.groupby(['year', 'week', 'subCategoryOf']).agg(
        total_sales=('totalProductPrice', 'sum')
    ).reset_index()

    # Calculate contribution percentage for each category
    total_weekly_sales = weekly_sales.groupby(['year', 'week'])['total_sales'].sum().reset_index()
    weekly_sales = weekly_sales.merge(total_weekly_sales, on=['year', 'week'], suffixes=('', '_total'))
    weekly_sales['contribution'] = (weekly_sales['total_sales'] / weekly_sales['total_sales_total']) * 100

    # Pivot the DataFrame to have weeks as columns
    weekly_contribution_df = weekly_sales.pivot(index='subCategoryOf', columns='week', values='contribution').reset_index()

    # Rename columns for clarity
    weekly_contribution_df.columns.name = None
    weeks_available = weekly_contribution_df.shape[1] - 1 
    weekly_contribution_df.columns = ['subCategoryOf'] + [f'week_{i}' for i in range(1, weeks_available + 1)]

    weeks_available = weekly_contribution_df.shape[1] - 1

    st.markdown("<h4 style='color: green; text-align: center;'>3 Week Average</h4>", unsafe_allow_html=True)


    if weeks_available >= 3:
        # Calculate the mean of available weeks
        if weeks_available >= 4:
            # Calculate for stores with at least 4 weeks of data
            weekly_contribution_df['3_week_average'] = weekly_contribution_df[[f'week_{i}' for i in range(1, 4)]].mean(axis=1)

            # Handle NaN and calculate difference and variance
            weekly_contribution_df['3_week_average'] = pd.to_numeric(weekly_contribution_df['3_week_average'], errors='coerce')
            weekly_contribution_df['3_week_average'].fillna(0, inplace=True)
            
            weekly_contribution_df['difference'] = weekly_contribution_df['3_week_average'] - weekly_contribution_df['week_4']
            weekly_contribution_df['variance'] = ((weekly_contribution_df['3_week_average'] - weekly_contribution_df['week_4']) / 
                                                weekly_contribution_df['week_4']) * 100
        else:
            # Handle the case with less than 4 weeks
            available_weeks = [f'week_{i}' for i in range(1, weeks_available + 1)]
            weekly_contribution_df['3_week_average'] = weekly_contribution_df[available_weeks].mean(axis=1)

            # Adjust variance calculation if there is no 'week_4'
            if 'week_4' in weekly_contribution_df.columns:
                weekly_contribution_df['difference'] = weekly_contribution_df['3_week_average'] - weekly_contribution_df['week_4']
                weekly_contribution_df['variance'] = ((weekly_contribution_df['3_week_average'] - weekly_contribution_df['week_4']) / 
                                                    weekly_contribution_df['week_4']) * 100
            else:
                weekly_contribution_df['difference'] = 0
                weekly_contribution_df['variance'] = 0

    if '3_week_average' not in weekly_contribution_df.columns:
        weekly_contribution_df['3_week_average'] = 0
 

    # Fill NaN values and format percentage columns
    weekly_contribution_df.fillna(0, inplace=True)

    # Format columns like 'week_4', 'variance', 'difference'
    for col in weekly_contribution_df.columns[1:]:
        if col in ['week_4', 'variance', 'difference'] or col.startswith('week_'):
            weekly_contribution_df[col] = weekly_contribution_df[col].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "0.00%")
        

    if top_n_comparison > 0:
        # Get the top N categories based on the 3-week average
        if '3_week_average' in weekly_contribution_df.columns:
            top_categories = weekly_contribution_df.nlargest(top_n_comparison, '3_week_average')
        else:
            print("Warning: '3_week_average' column is missing. Using all categories instead.")
            top_categories = weekly_contribution_df
    else:
        top_categories = weekly_contribution_df


    # Sidebar color options for the plot
    color_options = ['Purple','Blue', 'Orange', 'Green', 'Red', 'Brown']
    color_options_2 = ['Orange','Blue',  'Red','Green',  'Brown', 'Purple']
    selected_color_3w_avg = st.sidebar.selectbox("Select 3-Week Average Bar/Line Color:", color_options, key="color_3w_avg")
    selected_color_week_4 = st.sidebar.selectbox("Select Week 4 Contribution Bar/Line Color:", color_options_2, key="color_week_4")

    # Map color names to Plotly color codes
    color_mapping = {
        'Blue': 'blue', 
        'Orange': 'orange', 
        'Green': 'green', 
        'Red': 'red', 
        'Purple': 'purple', 
        'Brown': 'brown'
    }

    # Assign selected colors to each plot
    selected_color_1 = color_mapping[selected_color_3w_avg]
    selected_color_2 = color_mapping[selected_color_week_4]

    # Step 3: Plot comparing 3-week average and week 4 contribution
    if 'week_4' in top_categories.columns and '3_week_average' in top_categories.columns:
        fig_weekly = go.Figure()

        if plot_type_comparison == "Column Chart":
            # Add bars for Column Chart
            fig_weekly.add_trace(go.Bar(
                x=top_categories['subCategoryOf'],
                y=top_categories['3_week_average'],
                name='3 Week Average',
                marker_color=selected_color_1,
                text=top_categories['3_week_average'] if show_data_labels_comparison else None,
                textposition='auto'
            ))
            fig_weekly.add_trace(go.Bar(
                x=top_categories['subCategoryOf'],
                y=top_categories['week_4'],
                name='Week 4 Contribution',
                marker_color=selected_color_2,
                text=top_categories['week_4'] if show_data_labels_comparison else None,
                textposition='auto'
            ))

            fig_weekly.update_layout(
                title="Weekly Contribution Comparison (Column Chart)",
                xaxis_title="Category",
                yaxis_title="Contribution (%)",
                barmode='group',
                height=500,
                width=1100,
            )

        elif plot_type_comparison == "Line Chart":
            # Add lines for Line Chart
            fig_weekly.add_trace(go.Scatter(
                x=top_categories['subCategoryOf'],
                y=top_categories['3_week_average'],
                mode='lines+markers' if show_data_labels_comparison else 'lines',
                name='3 Week Average',
                line=dict(color=selected_color_1),
                text=top_categories['3_week_average'] if show_data_labels_comparison else None,
                textposition='top center'
            ))

            fig_weekly.add_trace(go.Scatter(
                x=top_categories['subCategoryOf'],
                y=top_categories['week_4'],
                mode='lines+markers' if show_data_labels_comparison else 'lines',
                name='Week 4 Contribution',
                line=dict(color=selected_color_2),
                text=top_categories['week_4'] if show_data_labels_comparison else None,
                textposition='top center'
            ))

            fig_weekly.update_layout(
                title="Weekly Contribution Comparison (Line Chart)",
                xaxis_title="Category",
                yaxis_title="Contribution (%)",
                height=500,
                width=1100,
            )

        # Ensure the chart is redrawn
        st.plotly_chart(fig_weekly)

    else:
        st.markdown("<h6 style='color: red; text-align: center;'>Insufficient data to calculate 3 week average</h6>", unsafe_allow_html=True)
        st.markdown("<hr style='border-top: 2px solid #bbb;'>", unsafe_allow_html=True)


    def highlight_negative(val):
        color = 'red' if isinstance(val, str) and '-' in val else ''
        return f'background-color: {color}'

    styled_df = weekly_contribution_df.style.applymap(highlight_negative, subset=['variance'])

    csv_week = convert_df(weekly_contribution_df)

    st.sidebar.download_button(
        label="Download weekly average Data",
        data=csv_week,
        file_name='weekly_contribution.csv',
        mime='text/csv',
    )

    # Store the results
    results['sales_per_category'] = sales_per_category


    return (
        results,
        #fig_category,
        final_df,
        results.get('store_kpis', {}),
        results.get('weekly_sales', {}).get('chart', None),
        results.get('weekly_sales', {}).get('data', None),
        results.get('monthly_sales', {}).get('chart', None),
        results.get('monthly_sales', {}).get('data', None),
        results.get('sales_comparison', {}).get('chart', None),
        results.get('sales_comparison', {}).get('data', None),
    )