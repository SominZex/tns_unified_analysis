import pandas as pd
import logging
from typing import Optional
import time
from sqlalchemy import create_engine
from datetime import datetime
from dateutil.relativedelta import relativedelta

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

DATABASE_URL = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

REQUIRED_COLUMNS = [
    "invoice", "productId", "orderDate", "time", "productName", "storeName",
    "sellingPrice", "costPrice", "quantity", "totalProductPrice",
    "brandName", "categoryName", "subCategoryOf",
    "orderType", "customerNumber", "discountAmount"]


def load_data_from_directory() -> pd.DataFrame:
    logger.info("Connecting to PostgreSQL and loading last 2 months of sales_data...")

    start_time = time.time()

    try:
        database_url = DATABASE_URL + "?sslmode=disable"

        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=1800
        )

        # Get the latest date from the database
        latest_date_query = f"""SELECT MAX("orderDate") FROM {PG_TABLE};"""
        latest_date = pd.read_sql(latest_date_query, engine).iloc[0, 0]

        if latest_date is None:
            raise ValueError("No data found in sales_data.")

        # Calculate start date: 2 months before the latest date
        start_date = latest_date - relativedelta(months=1)
        # Set to first day of that month for clean boundary
        start_date = start_date.replace(day=1)
        
        logger.info(f"Latest order date: {latest_date}, filtering from: {start_date} (last 2 months)")

        columns_str = ", ".join(f'"{col}"' for col in REQUIRED_COLUMNS)
        query = f"""
            SELECT {columns_str}
            FROM {PG_TABLE}
            WHERE "orderDate" >= '{start_date}';
        """
        
        def safe_read_sql(query: str, engine, chunksize=50000, retries=3, delay=2):
            for attempt in range(retries):
                try:
                    chunks = []
                    for chunk in pd.read_sql(query, engine, chunksize=chunksize):
                        chunks.append(chunk)
                    return pd.concat(chunks, ignore_index=True)
                except Exception as e:
                    logger.warning(f"Attempt {attempt+1}/{retries} failed: {e}")
                    last_exception = e
                    time.sleep(delay)
            logger.error(f"Final attempt failed with error: {last_exception}")
            raise last_exception

        # Use safe_read_sql
        df = safe_read_sql(query, engine)

        df.columns = df.columns.str.strip()
        logger.info(f"Loaded columns: {df.columns.tolist()}")

    except Exception as e:
        logger.error(f"PostgreSQL query failed: {e}")
        raise

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

    logger.info(f"Loaded {len(df)} rows from last 2 months in {time.time() - start_time:.2f} seconds.")
    logger.info(f"Data range: {df['orderDate'].min()} to {df['orderDate'].max()}")
    return df


def parse_time_dynamic(time_str) -> Optional[pd.Timestamp]:
    """Parse time string in various formats into Python time objects."""
    if pd.isna(time_str):
        return None
    formats = ['%H:%M:%S.%fZ', '%H:%M:%S', '%H:%M']
    for fmt in formats:
        try:
            return pd.to_datetime(time_str, format=fmt).time()
        except (ValueError, TypeError):
            continue
    return None
