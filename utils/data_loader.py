import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = "data"

def load_data_from_directory() -> pd.DataFrame:
    csv_files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
    if not csv_files:
        raise ValueError(f"No CSV files found in the '{DATA_DIR}' directory.")
    
    logger.info(f"Found {len(csv_files)} CSV files")
    
    data_frames: List[pd.DataFrame] = []
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            df.columns = df.columns.str.strip()
            data_frames.append(df)
        except Exception as e:
            logger.error(f"Error reading file {file}: {e}")

    if not data_frames:
        raise ValueError("No valid data was loaded from any CSV files.")
    
    all_columns = set().union(*[set(df.columns) for df in data_frames])
    required_columns = {'orderDate', 'time', 'productName', 'storeName', 
                        'sellingPrice', 'costPrice', 'quantity'}
    missing_columns = required_columns - all_columns

    for i, df in enumerate(data_frames):
        for col in missing_columns:
            if col not in df.columns:
                df[col] = None 

        df['orderDate'] = pd.to_datetime(df.get('orderDate'), errors='coerce', dayfirst=True)
        df['sellingPrice'] = pd.to_numeric(df.get('sellingPrice'), errors='coerce')
        df['costPrice'] = pd.to_numeric(df.get('costPrice'), errors='coerce')
        df['quantity'] = pd.to_numeric(df.get('quantity'), errors='coerce')
        df['productName'] = df.get('productName', '').astype(str).str.strip()
        df['storeName'] = df.get('storeName', '').astype(str).str.strip()

    combined_data = pd.concat(data_frames, ignore_index=True)
    combined_data = combined_data.drop_duplicates()
    combined_data = combined_data.sort_values(by=['orderDate']).reset_index(drop=True)
    
    logger.info(f"Successfully combined {len(csv_files)} files into a DataFrame with {len(combined_data)} rows.")
    return combined_data

def process_file(file_path: str) -> Optional[pd.DataFrame]:
    try:
        df = pd.read_csv(
            file_path,
            dtype={
                'productName': str,
                'storeName': str,
                'sellingPrice': float,
                'costPrice': float,
                'quantity': float
            },
            parse_dates=['orderDate'],
            dayfirst=True,
            encoding='utf-8'
        )
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

def parse_time_dynamic(time_str) -> Optional[pd.Timestamp]:
    """Parse time string in various formats."""
    if pd.isna(time_str):
        return None

    formats = ['%H:%M:%S.%fZ', '%H:%M:%S', '%H:%M']
    
    for fmt in formats:
        try:
            return pd.to_datetime(time_str, format=fmt).time()
        except (ValueError, TypeError):
            continue
    
    return None
