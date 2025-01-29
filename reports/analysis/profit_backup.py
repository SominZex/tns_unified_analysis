    overall_profit['total_profit_overall'] = overall_profit['total_sales_overall'] - overall_profit['total_cost_price_overall']

    # Calculate total profit per category for the selected store
    avg_profit_store = store_data.groupby('categoryName').agg(
        total_sales_store=('totalProductPrice', 'sum'),
        total_cost_price_store=('costPrice', 'sum')
    ).reset_index()

    avg_profit_store['total_profit_store'] = avg_profit_store['total_sales_store'] - avg_profit_store['total_cost_price_store']

    # Calculate total profit for the store
    total_profit_store = avg_profit_store['total_profit_store'].sum()

    # Calculate percentage contribution to total profit by category for the selected store
    avg_profit_store['percentage_contribution'] = (avg_profit_store['total_profit_store'] / total_profit_store) * 100

    # Merge store-specific and overall profit data
    profit_comparison_df = pd.merge(avg_profit_store[['categoryName', 'total_profit_store', 'percentage_contribution']],
                                    overall_profit[['categoryName', 'total_profit_overall']],
                                    on='categoryName', how='left')

    # Calculate percentage difference in profit
    profit_comparison_df['percentage_diff_profit'] = (
        (profit_comparison_df['total_profit_store'] - profit_comparison_df['total_profit_overall']) /
        profit_comparison_df['total_profit_overall']
    ) * 100

    # Calculate KPIs for profits
    store_average_profit = profit_comparison_df['total_profit_store'].mean()
    company_average_profit = profit_comparison_df['total_profit_overall'].mean()

    # Display KPIs for profit as cards
    st.markdown("<h2 style='color: green; text-align: center;'>Profit KPI</h2>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    # Store Average Profit
    average_profit = f"₹{store_average_profit:,.2f}"
    percentage_difference_profit = ((store_average_profit - company_average_profit) / company_average_profit) * 100
    display_profit_metric(col1, "Store Average Profit", average_profit, percentage_difference_profit)

    # Average Company Profit (instead of Total Company Profit)
    col2.metric("Average Company Profit", f"₹{company_average_profit:,.2f}")

    # Store Total Profit
    total_profit_formatted = f"₹{total_profit_store:,.2f}"
    col3.metric("Store Total Profit", total_profit_formatted)

    # Percentage Contribution to Total Profit
    average_percentage_contribution = avg_profit_store['percentage_contribution'].mean()
    col4.metric("Percentage Contribution to Total Profit", f"{average_percentage_contribution:.2f}%")

