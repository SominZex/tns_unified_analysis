import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def grn_analysis(sales_data, stock_data, selected_store):
    if stock_data is None:
        st.warning("Please upload stock data to perform Stock analysis.")
        return

    try:
        # Filter data for the selected store
        store_sales_data = sales_data[sales_data['storeName'] == selected_store].copy()
        store_stock_data = stock_data[stock_data['storeName'] == selected_store].copy()
        
        # Modified aggregation for sales data to ensure correct summing
        store_sales_data_agg = (store_sales_data.groupby(['productName', 'storeName'])
                               .agg({'quantity': 'sum'})
                               .reset_index()
                               .rename(columns={'quantity': 'quantity_sales'}))
        
        # Aggregate stock data by 'productName' and 'storeName'
        store_stock_data_agg = (store_stock_data.groupby(['productName', 'storeName'])
                               .agg({'quantity': 'sum'})
                               .reset_index()
                               .rename(columns={'quantity': 'quantity_stock'}))
     
        # Merge sales and stock data on 'productName' and 'storeName'
        merged_data = pd.merge(
            store_sales_data_agg,
            store_stock_data_agg,
            on=['productName', 'storeName'],
            how='outer'
        )
         
        # Handle missing values
        merged_data['quantity_sales'] = merged_data['quantity_sales'].fillna(0)
        merged_data['quantity_stock'] = merged_data['quantity_stock'].fillna(0)
        
        # Calculate discrepancies between stock and sales quantities
        merged_data['discrepancy'] = merged_data['quantity_stock'] - merged_data['quantity_sales']
        
        # Round up the discrepancy column
        merged_data['discrepancy'] = np.ceil(merged_data['discrepancy'])
        
        # Display analysis results
        st.markdown("<h4 style='color: green; text-align: center;'>Overall Report</h4>", unsafe_allow_html=True)
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)    
        with col1:
            st.metric("Total Products", len(merged_data))
        with col2:
            st.metric("Products with Discrepancies", 
                     len(merged_data[merged_data['discrepancy'] != 0]))
        with col3:
            accuracy_rate = (len(merged_data[merged_data['discrepancy'] == 0]) / 
                           len(merged_data) * 100)
            st.metric("Stock Accuracy Rate", f"{accuracy_rate:.2f}%")

        # Filter options
        discrepancy_filter = st.selectbox(
            "Filter by Discrepancy Type",
            ["All", "Over-stocked", "Under-stocked", "Matched"]
        )
        
        # Apply filters
        if discrepancy_filter == "Over-stocked":
            filtered_data = merged_data[merged_data['discrepancy'] > 0]
        elif discrepancy_filter == "Under-stocked":
            filtered_data = merged_data[merged_data['discrepancy'] < 0]
        elif discrepancy_filter == "Matched":
            filtered_data = merged_data[merged_data['discrepancy'] == 0]
        else:
            filtered_data = merged_data

        top_n = st.sidebar.number_input(
            "Select number of products to display",
            min_value=5,
            max_value=len(filtered_data),
            value=min(20, len(filtered_data)),
            step=5
        )
       
        # Display detailed table
        if not filtered_data.empty:
            display_columns = [
                'productName', 
                'quantity_sales',
                'quantity_stock', 
                'discrepancy'
            ]
            
            # Clean up display data
            display_data = filtered_data[display_columns].copy()
            display_data = display_data.replace({None: "N/A"})
            
            # Sort data from lowest to highest based on discrepancy
            display_data = display_data.sort_values('discrepancy', ascending=True)
            
            # Apply the top_n filter to the displayed dataframe
            display_data = display_data.head(top_n)
            display_data['quantity_stock'] = display_data['quantity_stock'].round(0).astype(int)
            display_data['discrepancy'] = display_data['discrepancy'].round(0).astype(int)

            st.table(display_data)
            
            # Enhanced Visualization
            if len(filtered_data) > 0:
                # Create tabs for different visualizations
                tab1, tab2 = st.tabs(["Discrepancy Analysis", "Stock vs Sales Comparison"])


                with tab1:
                    viz_data = filtered_data.nsmallest(top_n, 'discrepancy').copy()
                    viz_data = viz_data.sort_values(by='discrepancy', ascending=True)

                    # Create a waterfall chart with discrepancies in ascending order
                    fig = go.Figure(go.Waterfall(
                        name="Discrepancy",
                        orientation="v",
                        measure=["relative"] * len(viz_data),
                        x=viz_data['productName'],
                        y=viz_data['discrepancy'],
                        text=viz_data['discrepancy'].round(2),
                        textposition="outside",
                        connector={"line": {"color": "rgb(63, 63, 63)"}} ,
                        decreasing={"marker": {"color": "red"}},
                        increasing={"marker": {"color": "green"}},
                        totals={"marker": {"color": "blue"}}
                    ))

                    # Update layout to show sorted data from lowest to highest discrepancy
                    fig.update_layout(
                        title=f"Top {top_n} Products - Stock Discrepancy Analysis (Lowest to Highest)",
                        xaxis_title="Product Name",
                        yaxis_title="Quantity Discrepancy",
                        showlegend=False,
                        xaxis_tickangle=-45,
                        width=1000,
                        height=600
                    )

                    st.plotly_chart(fig, use_container_width=True)

                with tab2:
                    # Create a comparison bar chart using the same top_n products
                    comparison_fig = go.Figure()

                    comparison_fig.add_trace(go.Bar(
                        name='Stock Quantity',
                        x=viz_data['productName'],
                        y=viz_data['quantity_stock'],
                        marker_color='rgb(55, 83, 109)'
                    ))

                    comparison_fig.add_trace(go.Bar(
                        name='Sales Quantity',
                        x=viz_data['productName'],
                        y=viz_data['quantity_sales'],
                        marker_color='rgb(26, 118, 255)'
                    ))

                    comparison_fig.update_layout(
                        title=f'Stock vs Sales Quantity Comparison (Top {top_n} Products)',
                        xaxis_tickangle=-45,
                        xaxis_title="Product Name",
                        yaxis_title="Quantity",
                        barmode='group',
                        bargap=0.15,
                        bargroupgap=0.1,
                        width=1000,
                        height=600
                    )

                    st.plotly_chart(comparison_fig, use_container_width=True)
        
        # Out-of-stock products
        st.markdown("<h4 style='color: red; text-align: center;'>Out of stock products</h4>", unsafe_allow_html=True)
        out_of_stock = merged_data[merged_data['quantity_stock'] == 0]
        out_of_stock['quantity_stock'] = out_of_stock['quantity_stock'].round(0).astype(int)
        st.metric("Out-of-Stock Products", len(out_of_stock))
        st.table(out_of_stock[['productName', 'quantity_stock']].sort_values('quantity_stock', ascending=True).head(top_n))

        # Dead stock
        st.markdown("<h4 style='color: red; text-align: center;'>Dead Stocks</h4>", unsafe_allow_html=True)
        dead_stock = merged_data[(merged_data['quantity_stock'] > 0) & (merged_data['quantity_sales'] == 0)]
        st.metric("Dead Stock", len(dead_stock))
        st.table(dead_stock[['productName', 'quantity_stock', 'quantity_sales']].sort_values('quantity_stock', ascending=True).head(top_n))

        # Near out-of-stock products
        st.markdown("<h4 style='color: red; text-align: center;'>Near out of stock</h4>", unsafe_allow_html=True)
        threshold = 5
        near_out_of_stock = merged_data[(merged_data['quantity_stock'] < threshold) & (merged_data['quantity_stock'] > 0)]
        st.metric("Near Out-of-Stock Products", len(near_out_of_stock))
        st.table(near_out_of_stock[['productName', 'quantity_stock']].sort_values('quantity_stock', ascending=True).head(top_n))

        # Bad Inventory Management
        st.markdown("<h4 style='color: red; text-align: center;'>Bad Inventory Management</h4>", unsafe_allow_html=True)
        bad_inventory_management = merged_data[(merged_data['quantity_stock'] > 10 * merged_data['quantity_sales'])]
        st.metric("Poorly Managed Inventory Products", len(bad_inventory_management))
        st.table(bad_inventory_management[['productName', 'quantity_stock', 'quantity_sales']].sort_values('quantity_stock', ascending=True).head(top_n))

 



        # Aggregating sales data by 'brandName' and 'storeName'
        store_sales_data_agg_brand = (store_sales_data.groupby(['brandName', 'storeName'])
                               .agg({'quantity': 'sum'})
                               .reset_index()
                               .rename(columns={'quantity': 'quantity_sales', 'brandName': 'brand'}))
        
        # Aggregating stock data by 'brand' and 'storeName'
        store_stock_data_agg_brand = (store_stock_data.groupby(['brand', 'storeName'])
                               .agg({'quantity': 'sum', 'totalAmount': 'sum'})
                               .reset_index()
                               .rename(columns={'quantity': 'quantity_stock'}))
        
        # Merge sales and stock data on 'brand' and 'storeName'
        merged_data_brand = pd.merge(
            store_sales_data_agg_brand,
            store_stock_data_agg_brand,
            on=['brand', 'storeName'],
            how='outer'
        )
        
        # Handle missing values
        merged_data_brand['quantity_sales'] = merged_data_brand['quantity_sales'].fillna(0)
        merged_data_brand['quantity_stock'] = merged_data_brand['quantity_stock'].fillna(0)
        
        # Calculate discrepancies between stock and sales quantities
        merged_data_brand['discrepancy'] = merged_data_brand['quantity_stock'] - merged_data_brand['quantity_sales']
        merged_data_brand['discrepancy'] = np.ceil(merged_data_brand['discrepancy'])
        

        # Detailed analysis
        st.markdown("<h4 style='color: green; text-align: center;'>Detailed Stock Analysis by brand</h4>", unsafe_allow_html=True)
        
        # Filter options
        discrepancy_filter_brand = st.selectbox(
            "Filter by Discrepancy Type",
            ["All", "Over-stocked", "Under-stocked", "Matched"],
            key=f"discrepancy_filter_{selected_store}"
        )
        # Apply filters
        if discrepancy_filter_brand == "Over-stocked":
            filtered_data = merged_data_brand[merged_data_brand['discrepancy'] > 0]
        elif discrepancy_filter_brand == "Under-stocked":
            filtered_data = merged_data_brand[merged_data_brand['discrepancy'] < 0]
        elif discrepancy_filter_brand == "Matched":
            filtered_data = merged_data_brand[merged_data_brand['discrepancy'] == 0]
        else:
            filtered_data = merged_data_brand

        top_n_brand = st.sidebar.number_input(
            "Select number of brands to display",
            min_value=0,
            max_value=len(filtered_data),
            value=min(20, len(filtered_data)),
            step=5
        )
       
        # Display detailed table
        if not filtered_data.empty:
            display_columns = [
                'brand', 
                'quantity_sales',
                'quantity_stock', 
                'discrepancy'
            ]
            
            # Clean up display data
            display_data = filtered_data[display_columns].copy()
            display_data = display_data.replace({None: "N/A"})
            
            # Sort data from lowest to highest based on discrepancy
            display_data = display_data.sort_values('discrepancy', ascending=True)
            
            # Apply the top_n filter to the displayed dataframe
            display_data = display_data.head(top_n_brand)
            display_data['quantity_stock'] = display_data['quantity_stock'].round(0).astype(int)
            display_data['discrepancy'] = display_data['discrepancy'].round(0).astype(int)

            st.table(display_data)
            
            # Enhanced Visualization
            if len(filtered_data) > 0:
                # Create tabs for different visualizations
                tab1, tab2 = st.tabs(["Discrepancy Analysis", "Stock vs Sales Comparison"])

                with tab1:
                    viz_data = filtered_data.nsmallest(top_n_brand, 'discrepancy').copy()
                    viz_data = viz_data.sort_values(by='discrepancy', ascending=True)

                    # Create a waterfall chart with discrepancies in ascending order
                    fig = go.Figure(go.Waterfall(
                        name="Discrepancy",
                        orientation="v",
                        measure=["relative"] * len(viz_data),
                        x=viz_data['brand'],
                        y=viz_data['discrepancy'],
                        text=viz_data['discrepancy'].round(2),
                        textposition="outside",
                        connector={"line": {"color": "rgb(63, 63, 63)"}} ,
                        decreasing={"marker": {"color": "red"}},
                        increasing={"marker": {"color": "green"}},
                        totals={"marker": {"color": "blue"}}
                    ))

                    # Update layout to show sorted data from lowest to highest discrepancy
                    fig.update_layout(
                        title=f"Top {top_n} Brands - Stock Discrepancy Analysis (Lowest to Highest)",
                        xaxis_title="Brand",
                        yaxis_title="Quantity Discrepancy",
                        showlegend=False,
                        xaxis_tickangle=-45,
                        width=1000,
                        height=600
                    )

                    st.plotly_chart(fig, use_container_width=True)

                with tab2:
                    # Create a comparison bar chart using the same top_n products
                    comparison_fig = go.Figure()

                    comparison_fig.add_trace(go.Bar(
                        name='Stock Quantity',
                        x=viz_data['brand'],
                        y=viz_data['quantity_stock'],
                        marker_color='rgb(55, 83, 109)'
                    ))

                    comparison_fig.add_trace(go.Bar(
                        name='Sales Quantity',
                        x=viz_data['brand'],
                        y=viz_data['quantity_sales'],
                        marker_color='rgb(26, 118, 255)'
                    ))

                    comparison_fig.update_layout(
                        title=f'Stock vs Sales Quantity Comparison (Top {top_n_brand} Brands)',
                        xaxis_tickangle=-45,
                        xaxis_title="Brand",
                        yaxis_title="Quantity",
                        barmode='group',
                        bargap=0.15,
                        bargroupgap=0.1,
                        width=1000,
                        height=600
                    )

                    st.plotly_chart(comparison_fig, use_container_width=True)
        
        # Out-of-stock products
        st.markdown("<h4 style='color: red; text-align: center;'>Out of stock brands</h4>", unsafe_allow_html=True)
        out_of_stock_brands = merged_data_brand[merged_data_brand['quantity_stock'] == 0]
        out_of_stock_brands['quantity_stock'] = out_of_stock_brands['quantity_stock'].round(0).astype(int)
        st.metric("Out-of-Stock brands", len(out_of_stock_brands))
        st.table(out_of_stock_brands[['brand', 'quantity_stock']].sort_values('quantity_stock', ascending=True).head(top_n_brand))

        # Dead stock
        st.markdown("<h4 style='color: red; text-align: center;'>Dead Stocks</h4>", unsafe_allow_html=True)
        dead_stock_brands = merged_data_brand[(merged_data_brand['quantity_stock'] > 0) & (merged_data_brand['quantity_sales'] == 0)]
        st.metric("Dead Stock", len(dead_stock_brands))
        st.table(dead_stock_brands[['brand', 'quantity_stock', 'quantity_sales']].sort_values('quantity_stock', ascending=True).head(top_n_brand))

        # Near out-of-stock products
        st.markdown("<h4 style='color: red; text-align: center;'>Near out of stock</h4>", unsafe_allow_html=True)
        threshold = 5
        near_out_of_stock_brand = merged_data_brand[(merged_data_brand['quantity_stock'] < threshold) & (merged_data_brand['quantity_stock'] > 0)]
        st.metric("Near Out-of-Stock Products", len(near_out_of_stock_brand))
        st.table(near_out_of_stock_brand[['brand', 'quantity_stock']].sort_values('quantity_stock', ascending=True).head(top_n_brand))

        # Bad Inventory Management
        st.markdown("<h4 style='color: red; text-align: center;'>Bad Inventory Management</h4>", unsafe_allow_html=True)
        bad_inventory_management_brand = merged_data_brand[(merged_data_brand['quantity_stock'] > 0) & (merged_data_brand['quantity_sales'] == 0)]
        st.metric("Bad Inventory Management", len(bad_inventory_management_brand))
        st.table(bad_inventory_management_brand[['brand', 'quantity_stock', 'quantity_sales']].sort_values('quantity_stock', ascending=True).head(top_n_brand))


    except Exception as e:
        st.error(f"An error occurred during GRN analysis: {str(e)}")
        st.write("Please ensure your data contains the required columns and proper format.")

def upload_stock_data():
    """Upload and validate stock data file"""
    stock_file = st.file_uploader("Upload Stock CSV file (for Stock Analysis)", type="csv")
    
    if stock_file is not None:
        try:
            stock_data = pd.read_csv(stock_file)
            required_columns = ['productId', 'storeName', 'quantity']
            
            # Validate required columns
            if not all(col in stock_data.columns for col in required_columns):
                st.error("Stock data must contain: productId, storeName, and quantity columns")
                return None

            return stock_data

        except Exception as e:
            st.error(f"Error processing stock data: {str(e)}")
            return None

    return None
