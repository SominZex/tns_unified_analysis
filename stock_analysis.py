import pandas as pd
import numpy as np
from datetime import datetime
import os

def load_and_clean_data(file1_path, file2_path):
    """
    Load CSV files and clean column names
    """
    try:
        # Read CSV files
        store1_df = pd.read_csv(file1_path)
        store2_df = pd.read_csv(file2_path)
        
        # Clean column names (remove extra spaces)
        store1_df.columns = store1_df.columns.str.strip()
        store2_df.columns = store2_df.columns.str.strip()
        
        # Get store names from the data
        store1_name = store1_df['storeName'].iloc[0] if 'storeName' in store1_df.columns else 'Store1'
        store2_name = store2_df['storeName'].iloc[0] if 'storeName' in store2_df.columns else 'Store2'
        
        print(f"Loaded data for {store1_name}: {len(store1_df)} products")
        print(f"Loaded data for {store2_name}: {len(store2_df)} products")
        
        return store1_df, store2_df, store1_name, store2_name
        
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return None, None, None, None

def brand_wise_comparison(store1_df, store2_df, store1_name, store2_name):
    """
    Compare stock brand-wise between two stores
    """
    # Group by brand and sum quantities
    store1_brand = store1_df.groupby('brand').agg({
        'quantity': 'sum',
        'totalAmount': 'sum',
        'productId': 'count'
    }).rename(columns={'productId': 'product_count'})
    
    store2_brand = store2_df.groupby('brand').agg({
        'quantity': 'sum',
        'totalAmount': 'sum',
        'productId': 'count'
    }).rename(columns={'productId': 'count'})
    
    # Merge the data
    brand_comparison = pd.merge(
        store1_brand, store2_brand, 
        left_index=True, right_index=True, 
        how='outer', suffixes=(f'_{store1_name}', f'_{store2_name}')
    ).fillna(0)
    
    # Calculate differences
    brand_comparison[f'quantity_diff_{store1_name}_vs_{store2_name}'] = (
        brand_comparison[f'quantity_{store1_name}'] - brand_comparison[f'quantity_{store2_name}']
    )
    
    brand_comparison[f'amount_diff_{store1_name}_vs_{store2_name}'] = (
        brand_comparison[f'totalAmount_{store1_name}'] - brand_comparison[f'totalAmount_{store2_name}']
    )
    
    # Reset index to make brand a column
    brand_comparison = brand_comparison.reset_index()
    
    return brand_comparison

def product_wise_comparison(store1_df, store2_df, store1_name, store2_name):
    """
    Compare stock product-wise between two stores
    """
    # Select relevant columns for comparison
    cols = ['productId', 'productName', 'barcode', 'brand', 'categoryName', 
            'quantity', 'sellingPrice', 'totalAmount']
    
    store1_products = store1_df[cols].copy()
    store2_products = store2_df[cols].copy()
    
    # Merge on productId (or barcode if productId is not unique)
    product_comparison = pd.merge(
        store1_products, store2_products,
        on=['productId', 'productName', 'barcode'], 
        how='outer', suffixes=(f'_{store1_name}', f'_{store2_name}')
    )
    
    # Fill NaN values with 0 for numeric columns
    numeric_cols = ['quantity', 'sellingPrice', 'totalAmount']
    for col in numeric_cols:
        product_comparison[f'{col}_{store1_name}'] = product_comparison[f'{col}_{store1_name}'].fillna(0)
        product_comparison[f'{col}_{store2_name}'] = product_comparison[f'{col}_{store2_name}'].fillna(0)
    
    # Calculate differences
    product_comparison[f'quantity_diff_{store1_name}_vs_{store2_name}'] = (
        product_comparison[f'quantity_{store1_name}'] - product_comparison[f'quantity_{store2_name}']
    )
    
    product_comparison[f'amount_diff_{store1_name}_vs_{store2_name}'] = (
        product_comparison[f'totalAmount_{store1_name}'] - product_comparison[f'totalAmount_{store2_name}']
    )
    
    # Add availability flags
    product_comparison[f'available_in_{store1_name}'] = product_comparison[f'quantity_{store1_name}'] > 0
    product_comparison[f'available_in_{store2_name}'] = product_comparison[f'quantity_{store2_name}'] > 0
    product_comparison['available_in_both'] = (
        product_comparison[f'available_in_{store1_name}'] & 
        product_comparison[f'available_in_{store2_name}']
    )
    
    return product_comparison

def category_wise_comparison(store1_df, store2_df, store1_name, store2_name):
    """
    Compare stock category-wise between two stores
    """
    # Group by category
    store1_cat = store1_df.groupby('categoryName').agg({
        'quantity': 'sum',
        'totalAmount': 'sum',
        'productId': 'count',
        'brand': 'nunique'
    }).rename(columns={'productId': 'product_count', 'brand': 'brand_count'})
    
    store2_cat = store2_df.groupby('categoryName').agg({
        'quantity': 'sum',
        'totalAmount': 'sum',
        'productId': 'count',
        'brand': 'nunique'
    }).rename(columns={'productId': 'product_count', 'brand': 'brand_count'})
    
    # Merge the data
    category_comparison = pd.merge(
        store1_cat, store2_cat,
        left_index=True, right_index=True,
        how='outer', suffixes=(f'_{store1_name}', f'_{store2_name}')
    ).fillna(0)
    
    # Calculate differences
    category_comparison[f'quantity_diff_{store1_name}_vs_{store2_name}'] = (
        category_comparison[f'quantity_{store1_name}'] - category_comparison[f'quantity_{store2_name}']
    )
    
    category_comparison = category_comparison.reset_index()
    
    return category_comparison

def stock_availability_analysis(store1_df, store2_df, store1_name, store2_name):
    """
    Analyze products that are available in one store but not in another
    """
    # Products only in store1
    store1_products = set(store1_df['productId'].unique())
    store2_products = set(store2_df['productId'].unique())
    
    only_store1 = store1_products - store2_products
    only_store2 = store2_products - store1_products
    common_products = store1_products & store2_products
    
    # Create dataframes for products unique to each store
    unique_to_store1 = store1_df[store1_df['productId'].isin(only_store1)][
        ['productId', 'productName', 'brand', 'categoryName', 'quantity', 'totalAmount']
    ].copy()
    unique_to_store1['status'] = f'Only in {store1_name}'
    
    unique_to_store2 = store2_df[store2_df['productId'].isin(only_store2)][
        ['productId', 'productName', 'brand', 'categoryName', 'quantity', 'totalAmount']
    ].copy()
    unique_to_store2['status'] = f'Only in {store2_name}'
    
    # Combine unique products
    unique_products = pd.concat([unique_to_store1, unique_to_store2], ignore_index=True)
    
    # Summary statistics
    summary = pd.DataFrame({
        'Metric': [
            f'Products only in {store1_name}',
            f'Products only in {store2_name}',
            'Common products',
            f'Total unique products in {store1_name}',
            f'Total unique products in {store2_name}'
        ],
        'Count': [
            len(only_store1),
            len(only_store2),
            len(common_products),
            len(store1_products),
            len(store2_products)
        ]
    })
    
    return unique_products, summary

def low_stock_analysis(store1_df, store2_df, store1_name, store2_name, threshold=10):
    """
    Identify products with low stock in either store
    """
    # Low stock in store1
    low_stock_store1 = store1_df[store1_df['quantity'] <= threshold][
        ['productId', 'productName', 'brand', 'categoryName', 'quantity', 'sellingPrice']
    ].copy()
    low_stock_store1['store'] = store1_name
    low_stock_store1['stock_status'] = 'Low Stock'
    
    # Low stock in store2
    low_stock_store2 = store2_df[store2_df['quantity'] <= threshold][
        ['productId', 'productName', 'brand', 'categoryName', 'quantity', 'sellingPrice']
    ].copy()
    low_stock_store2['store'] = store2_name
    low_stock_store2['stock_status'] = 'Low Stock'
    
    # Combine low stock data
    low_stock_combined = pd.concat([low_stock_store1, low_stock_store2], ignore_index=True)
    
    return low_stock_combined

def generate_summary_report(brand_comp, product_comp, category_comp, store1_name, store2_name):
    """
    Generate overall summary report
    """
    summary_data = []
    
    # Brand summary
    total_brands_store1 = len(brand_comp[brand_comp[f'quantity_{store1_name}'] > 0])
    total_brands_store2 = len(brand_comp[brand_comp[f'quantity_{store2_name}'] > 0])
    common_brands = len(brand_comp[
        (brand_comp[f'quantity_{store1_name}'] > 0) & 
        (brand_comp[f'quantity_{store2_name}'] > 0)
    ])
    
    summary_data.extend([
        ['Total Brands', store1_name, total_brands_store1],
        ['Total Brands', store2_name, total_brands_store2],
        ['Common Brands', 'Both Stores', common_brands]
    ])
    
    # Product summary
    total_products_store1 = len(product_comp[product_comp[f'quantity_{store1_name}'] > 0])
    total_products_store2 = len(product_comp[product_comp[f'quantity_{store2_name}'] > 0])
    common_products = len(product_comp[product_comp['available_in_both']])
    
    summary_data.extend([
        ['Total Products', store1_name, total_products_store1],
        ['Total Products', store2_name, total_products_store2],
        ['Common Products', 'Both Stores', common_products]
    ])
    
    # Quantity summary
    total_qty_store1 = brand_comp[f'quantity_{store1_name}'].sum()
    total_qty_store2 = brand_comp[f'quantity_{store2_name}'].sum()
    
    summary_data.extend([
        ['Total Quantity', store1_name, total_qty_store1],
        ['Total Quantity', store2_name, total_qty_store2],
        ['Quantity Difference', f'{store1_name} - {store2_name}', total_qty_store1 - total_qty_store2]
    ])
    
    summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Store', 'Value'])
    
    return summary_df

def main():
    """
    Main function to run the complete stock comparison analysis
    """
    # Check if stock directory exists
    stock_dir = "stock"
    if os.path.exists(stock_dir):
        print(f"Found stock directory: {stock_dir}")
        print("Available CSV files:")
        csv_files = [f for f in os.listdir(stock_dir) if f.endswith('.csv')]
        for i, file in enumerate(csv_files, 1):
            print(f"{i}. {file}")
        
        if len(csv_files) >= 2:
            print("\nYou can either:")
            print("1. Enter file numbers (e.g., '1' and '2')")
            print("2. Enter full file paths")
            
            file1_input = input("Enter Store 1 file (number or path): ").strip()
            file2_input = input("Enter Store 2 file (number or path): ").strip()
            
            # Check if inputs are numbers
            try:
                file1_idx = int(file1_input) - 1
                file1_path = os.path.join(stock_dir, csv_files[file1_idx])
            except (ValueError, IndexError):
                file1_path = file1_input if not file1_input.startswith('stock/') else file1_input
                if not file1_path.startswith('stock/') and not os.path.exists(file1_path):
                    file1_path = os.path.join(stock_dir, file1_input)
            
            try:
                file2_idx = int(file2_input) - 1
                file2_path = os.path.join(stock_dir, csv_files[file2_idx])
            except (ValueError, IndexError):
                file2_path = file2_input if not file2_input.startswith('stock/') else file2_input
                if not file2_path.startswith('stock/') and not os.path.exists(file2_path):
                    file2_path = os.path.join(stock_dir, file2_input)
        else:
            print("Please provide the full paths to your CSV files:")
            file1_path = input("Enter the path to Store 1 CSV file: ").strip()
            file2_path = input("Enter the path to Store 2 CSV file: ").strip()
    else:
        print("Stock directory not found. Please provide the full paths to your CSV files:")
        file1_path = input("Enter the path to Store 1 CSV file: ").strip()
        file2_path = input("Enter the path to Store 2 CSV file: ").strip()
    
    # Load data
    store1_df, store2_df, store1_name, store2_name = load_and_clean_data(file1_path, file2_path)
    
    if store1_df is None or store2_df is None:
        print("Failed to load data. Please check file paths and try again.")
        return
    
    print(f"\nStarting comparison analysis between {store1_name} and {store2_name}...")
    
    # Create output directory
    output_dir = f"stock_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 1. Brand-wise comparison
        print("Generating brand-wise comparison...")
        brand_comparison = brand_wise_comparison(store1_df, store2_df, store1_name, store2_name)
        brand_comparison.to_csv(f"{output_dir}/brand_wise_comparison.csv", index=False)
        
        # 2. Product-wise comparison
        print("Generating product-wise comparison...")
        product_comparison = product_wise_comparison(store1_df, store2_df, store1_name, store2_name)
        product_comparison.to_csv(f"{output_dir}/product_wise_comparison.csv", index=False)
        
        # 3. Category-wise comparison
        print("Generating category-wise comparison...")
        category_comparison = category_wise_comparison(store1_df, store2_df, store1_name, store2_name)
        category_comparison.to_csv(f"{output_dir}/category_wise_comparison.csv", index=False)
        
        # 4. Stock availability analysis
        print("Analyzing stock availability...")
        unique_products, availability_summary = stock_availability_analysis(
            store1_df, store2_df, store1_name, store2_name
        )
        unique_products.to_csv(f"{output_dir}/unique_products_analysis.csv", index=False)
        availability_summary.to_csv(f"{output_dir}/availability_summary.csv", index=False)
        
        # 5. Low stock analysis
        print("Analyzing low stock products...")
        low_stock_threshold = int(input("Enter low stock threshold (default 10): ") or "10")
        low_stock_analysis_df = low_stock_analysis(
            store1_df, store2_df, store1_name, store2_name, low_stock_threshold
        )
        low_stock_analysis_df.to_csv(f"{output_dir}/low_stock_analysis.csv", index=False)
        
        # 6. Generate summary report
        print("Generating summary report...")
        summary_report = generate_summary_report(
            brand_comparison, product_comparison, category_comparison, store1_name, store2_name
        )
        summary_report.to_csv(f"{output_dir}/summary_report.csv", index=False)
        
        # 7. Top performing brands/categories by quantity
        print("Generating top performers analysis...")
        
        # Top brands by quantity
        top_brands_store1 = brand_comparison.nlargest(10, f'quantity_{store1_name}')[
            ['brand', f'quantity_{store1_name}', f'totalAmount_{store1_name}']
        ]
        top_brands_store2 = brand_comparison.nlargest(10, f'quantity_{store2_name}')[
            ['brand', f'quantity_{store2_name}', f'totalAmount_{store2_name}']
        ]
        
        top_brands_store1.to_csv(f"{output_dir}/top_brands_{store1_name}.csv", index=False)
        top_brands_store2.to_csv(f"{output_dir}/top_brands_{store2_name}.csv", index=False)
        
        print(f"\nAnalysis complete! All reports saved in '{output_dir}' directory.")
        print("\nGenerated files:")
        print("1. brand_wise_comparison.csv - Brand level stock comparison")
        print("2. product_wise_comparison.csv - Product level detailed comparison")
        print("3. category_wise_comparison.csv - Category level comparison")
        print("4. unique_products_analysis.csv - Products unique to each store")
        print("5. availability_summary.csv - Stock availability summary")
        print("6. low_stock_analysis.csv - Low stock products identification")
        print("7. summary_report.csv - Overall comparison summary")
        print(f"8. top_brands_{store1_name}.csv - Top performing brands in {store1_name}")
        print(f"9. top_brands_{store2_name}.csv - Top performing brands in {store2_name}")
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        return

if __name__ == "__main__":
    main()