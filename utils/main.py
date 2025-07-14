import pandas as pd
from data_loader import load_data_from_directory

def main():
    df = load_data_from_directory()
    
    # Check the shape and date range of your data
    print(f"Total rows loaded: {len(df)}")
    print(f"Date range: {df['orderDate'].min()} to {df['orderDate'].max()}")
    print(f"Unique dates count: {df['orderDate'].nunique()}")
    
    # Show date distribution
    date_counts = df['orderDate'].value_counts().sort_index()
    print("\nDate distribution (first 10 and last 10):")
    print(date_counts.head(10))
    print("...")
    print(date_counts.tail(10))

if __name__ == "__main__":
    main()