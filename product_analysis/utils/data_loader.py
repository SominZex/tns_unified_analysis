import os
import pandas as pd
import streamlit as st
from concurrent.futures import ThreadPoolExecutor

DATA_DIR = "data"

# Optimized function to load data using parallel processing
def load_data_from_directory():
    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]

    if not csv_files:
        st.error("No CSV files found in the 'data' directory.")
        return None

    # Function to process a single CSV file
    def process_file(file):
        file_path = os.path.join(DATA_DIR, file)
        try:
            df = pd.read_csv(file_path, parse_dates=['orderDate'], dayfirst=True)
            df['time'] = df['time'].apply(parse_time_dynamic)
            return df
        except Exception as e:
            st.error(f"Error loading {file}: {e}")
            return None

    # Use ThreadPoolExecutor to load files concurrently
    with ThreadPoolExecutor() as executor:
        data_frames = list(executor.map(process_file, csv_files))

    # Filter out any None values returned in case of errors
    data_frames = [df for df in data_frames if df is not None]

    if data_frames:
        full_data = pd.concat(data_frames, ignore_index=True)
        return full_data
    else:
        return None

def parse_time_dynamic(time_str):
    try:
        return pd.to_datetime(time_str, format='%H:%M:%S.%fZ').time()
    except ValueError:
        try:
            return pd.to_datetime(time_str, format='%H:%M:%S').time()
        except ValueError:
            try:
                return pd.to_datetime(time_str, format='%H:%M').time()
            except ValueError:
                return None

# Optimized data loader function
@st.cache_data
def load_optimized_data_from_directory():
    return load_data_from_directory()

data = load_optimized_data_from_directory()

if data is not None:
    st.session_state.data = data
else:
    st.warning("No data was loaded from the directory.")

