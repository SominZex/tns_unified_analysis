import pandas as pd
from sqlalchemy import create_engine

# --- CONFIGURATION ---
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "root"
DB_NAME = "sales_data"

# --- SQL QUERY ---
query = 'SELECT * FROM sales_data WHERE brandName = "Nestle"'

def main():
    # Create SQLAlchemy engine
    engine = create_engine(
        f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # Fetch data
    df = pd.read_sql_query(query, engine)

    # Export to CSV
    output_file = "nestle_sales.csv"
    df.to_csv(output_file, index=False)
    print(f"Exported {len(df)} records to {output_file}")

if __name__ == "__main__":
    main()