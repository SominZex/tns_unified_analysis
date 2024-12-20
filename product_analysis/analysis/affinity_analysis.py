import pandas as pd
import itertools
from collections import Counter
import streamlit as st

def affinity_analysis(data):
    # Extract relevant columns (invoice, productId, productName, and time) from the data
    transaction_data = data[['invoice', 'productId', 'productName', 'time']]

    # Ensure the 'time' column is parsed as datetime
    try:
        transaction_data['time'] = pd.to_datetime(transaction_data['time'], errors='coerce')
    except Exception as e:
        st.warning("Time column contains invalid or inconsistent formats. Proceeding without time-based filtering.")
        transaction_data['time'] = pd.NaT

    # Drop rows with missing productId or invoice (essential for analysis)
    transaction_data = transaction_data.dropna(subset=['productId', 'invoice'])

    cooccurrence = Counter()

    for invoice, group in transaction_data.groupby('invoice'):
        product_ids = group['productId'].tolist()
        if len(product_ids) > 1:
            for r in range(2,  4):
                product_combinations = itertools.combinations(sorted(product_ids), r)
                cooccurrence.update(product_combinations)

    # Step 3: Convert co-occurrence dictionary to a DataFrame for easier analysis
    cooccurrence_df = pd.DataFrame(cooccurrence.items(), columns=['product_combination', 'frequency'])

    if not cooccurrence_df.empty:
        max_combination_size = cooccurrence_df['product_combination'].apply(len).max()

        product_combinations_df = pd.DataFrame(
            cooccurrence_df['product_combination'].tolist(),
            columns=[f'product_{i+1}' for i in range(max_combination_size)]
        )

        cooccurrence_df = pd.concat([product_combinations_df, cooccurrence_df['frequency']], axis=1)

        columns = ['frequency'] + [col for col in cooccurrence_df.columns if col != 'frequency']
        cooccurrence_df = cooccurrence_df[columns]

        cooccurrence_df = cooccurrence_df.sort_values(by='frequency', ascending=False).reset_index(drop=True)
    else:
        st.warning("No product combinations found. Please check your data.")

    # Map the productId to productName for displaying in the selectbox
    product_name_map = dict(zip(transaction_data['productId'], transaction_data['productName']))
    unique_product_names = sorted(transaction_data['productName'].unique())

    # Let the user select a product by its name
    selected_product_name = st.selectbox(
        "Select a Product for Affinity Analysis",
        options=["All Products"] + unique_product_names,
        index=1
    )

    if selected_product_name == "All Products":
        filtered_df = cooccurrence_df.copy()

        for col in filtered_df.columns[1:]:
            filtered_df[col] = filtered_df[col].map(product_name_map)
    else:
        selected_product_id = [product_id for product_id, product_name in product_name_map.items() if product_name == selected_product_name][0]

        filtered_df = cooccurrence_df[
            cooccurrence_df.apply(lambda row: selected_product_id in row.values[1:], axis=1)
        ]

        for col in filtered_df.columns[1:]:
            filtered_df[col] = filtered_df[col].map(product_name_map)

    if selected_product_name == "All Products":
        st.subheader("All frequently bought product combinations")
    else:
        st.subheader(f"Products frequently bought with '{selected_product_name}'")

    st.write(filtered_df)
