import pandas as pd
import logging
from sqlalchemy import create_engine
from typing import Optional

# ───── Logging Setup ─────
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ───── PostgreSQL Config ─────
DB_USER     = "user"
DB_PASSWORD = "pw"
DB_HOST     = "ip"
DB_PORT     = "port"
DB_NAME     = "db_name"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ───── Required Columns ─────
REQUIRED_COLUMNS = {
    'orderDate', 'time', 'productName', 'storeName',
    'sellingPrice', 'costPrice', 'quantity'
}


def load_data_from_directory() -> pd.DataFrame:
    """
    Replacement for the original CSV loader — now loads from PostgreSQL `sales_data` table.
    Preserves all data transformations and logging structure.
    """
    logger.info("Connecting to PostgreSQL and loading sales_data table...")

    try:
        engine = create_engine(DATABASE_URL)
        df = pd.read_sql("SELECT * FROM sales_data", engine)
        df.columns = df.columns.str.strip()
    except Exception as e:
        logger.error(f"Error querying database: {e}")
        raise

    # Ensure all required columns exist
    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    for col in missing_columns:
        df[col] = None

    # Data type conversions
    df['orderDate']    = pd.to_datetime(df.get('orderDate'), errors='coerce', dayfirst=True)
    df['sellingPrice'] = pd.to_numeric(df.get('sellingPrice'), errors='coerce')
    df['costPrice']    = pd.to_numeric(df.get('costPrice'), errors='coerce')
    df['quantity']     = pd.to_numeric(df.get('quantity'), errors='coerce')
    df['productName']  = df.get('productName', '').astype(str).str.strip()
    df['storeName']    = df.get('storeName', '').astype(str).str.strip()

    # Parse time column safely
    df['time'] = df['time'].apply(parse_time_dynamic)

    # Clean and finalize
    df = df.drop_duplicates()
    df = df.sort_values(by=['orderDate']).reset_index(drop=True)

    logger.info(f"Loaded {len(df)} rows from PostgreSQL.")
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