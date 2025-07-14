import pandas as pd
import streamlit as st
from dateutil import parser

def parse_date_dynamic(date_str):
    """
    Tries to parse a date string using dateutil.parser for maximum flexibility.
    Returns pd.NaT if parsing fails.
    """
    try:
        return parser.parse(str(date_str), dayfirst=False, fuzzy=True)
    except Exception:
        try:
            # Try with dayfirst=True as a fallback
            return parser.parse(str(date_str), dayfirst=True, fuzzy=True)
        except Exception:
            return pd.NaT

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

def load_data(uploaded_file):
    data = pd.read_csv(uploaded_file)
    # Apply robust date parsing to each value in the orderDate column
    data['orderDate'] = data['orderDate'].apply(parse_date_dynamic)
    data['time'] = data['time'].apply(parse_time_dynamic)
    return data