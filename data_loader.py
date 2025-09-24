import pandas as pd
import logging
from typing import Optional
import time
import psycopg2
from sqlalchemy import create_engine
from datetime import datetime

# ───── Logging Setup ─────
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ───── PostgreSQL Config ─────
PG_HOST = 'host_ip'
PG_PORT = 'post_no'
PG_DB = 'db_name'
PG_USER = 'user_name'
PG_PASSWORD = 'pw'
PG_TABLE = 'table'

# ───── Required Columns ─────
REQUIRED_COLUMNS = {
    "invoice", 'productId', 'orderDate', 'time', 'productName', 'storeName',
    'sellingPrice', 'costPrice', 'quantity', 'totalProductPrice',
    'brandName', 'categoryName', 'subCategoryOf',
    'orderType', 'customerNumber', 'discountAmount'
}

def load_data_from_directory() -> pd.DataFrame:
    logger.info("Connecting to PostgreSQL and loading data for the latest month...")
    start_time = time.time()

    try:
        engine = create_engine(
            f'postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}'
        )

        # Step 1: Get latest orderDate
        latest_date_query = f"SELECT MAX(orderDate) FROM {PG_TABLE};"
        latest_date = pd.read_sql(latest_date_query, engine).iloc[0, 0]

        if latest_date is None:
            raise ValueError("No data found in sales_data.")
        start_of_month = latest_date.replace(day=1)

        # Step 2: Query current month data
        column_str = ", ".join(REQUIRED_COLUMNS)
        query = f"""
            SELECT {column_str}
            FROM {PG_TABLE}
            WHERE orderDate >= '{start_of_month}'
        """
        df = pd.read_sql(query, engine)
        logger.info(f"Loaded columns: {df.columns.tolist()}")

    except Exception as e:
        logger.error(f"PostgreSQL query failed: {e}")
        raise

    # ───── Data Cleaning ─────
    df.columns = df.columns.str.strip()

    if 'orderDate' in df.columns:
        df['orderDate'] = pd.to_datetime(df['orderDate'], errors='coerce').dt.tz_localize(None)

    for col in ['sellingPrice', 'costPrice', 'quantity', 'totalProductPrice', 'discountAmount']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    for col in [
        'invoice', 'productId', 'productName', 'storeName',
        'brandName', 'categoryName', 'subCategoryOf',
        'orderType', 'customerNumber'
    ]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        else:
            df[col] = ''

    if 'time' in df.columns:
        df['time'] = df['time'].apply(parse_time_dynamic)

    df.drop_duplicates(inplace=True)
    df.sort_values(by='orderDate', inplace=True)
    df.reset_index(drop=True, inplace=True)

    logger.info(f"Loaded {len(df)} rows from {start_of_month.strftime('%B %Y')} in {time.time() - start_time:.2f} seconds.")
    return df


def parse_time_dynamic(time_str) -> Optional[pd.Timestamp]:
    if pd.isna(time_str):
        return None
    formats = ['%H:%M:%S.%fZ', '%H:%M:%S', '%H:%M']
    for fmt in formats:
        try:
            return pd.to_datetime(time_str, format=fmt).time()
        except (ValueError, TypeError):
            continue
    return None
