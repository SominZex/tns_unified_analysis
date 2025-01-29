import pandas as pd
import itertools
from collections import Counter
import streamlit as st

def affinity_analysis(data, selected_product_sidebar=None, top_n=20):
    # Get the top-n products from the data
    top_products = data['productName'].value_counts().head(top_n).index.tolist()

    transaction_data = data[['invoice', 'productId', 'productName', 'time']]

    try:
        transaction_data['time'] = pd.to_datetime(transaction_data['time'], errors='coerce')
    except Exception as e:
        st.warning("Time column contains invalid or inconsistent formats. Proceeding without time-based filtering.")
        transaction_data['time'] = pd.NaT

    transaction_data = transaction_data.dropna(subset=['productId', 'invoice'])

    # Normalize product names for filtering based on selected products
    product_name_map = dict(zip(transaction_data['productId'], transaction_data['productName'].str.strip().str.lower()))

    # Filter based on top-n products (if specified) and selected products
    if top_n is not None:
        # Filter transaction data to include only top-n products
        transaction_data = transaction_data[transaction_data['productName'].isin(top_products)]

    if selected_product_sidebar:
        # Normalize each selected product in the sidebar
        selected_product_names_normalized = [product.strip().lower() for product in selected_product_sidebar]
        selected_product_ids = []

        # Check if the selected product exists in the product_name_map
        for product_id, product_name in product_name_map.items():
            if product_name in selected_product_names_normalized:
                selected_product_ids.append(product_id)

        if not selected_product_ids:
            st.warning(f"Selected product(s) '{', '.join(selected_product_sidebar)}' not found in the data.")
            return
    else:
        selected_product_ids = product_name_map.keys() 

    cooccurrence = Counter()

    for invoice, group in transaction_data.groupby('invoice'):
        product_ids = group['productId'].tolist()
        if len(product_ids) > 1:
            # Generate combinations of products (size 2 to 3)
            for r in range(2, 4):
                product_combinations = itertools.combinations(sorted(product_ids), r)
                cooccurrence.update(product_combinations)

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

        cooccurrence_df = cooccurrence_df[
            cooccurrence_df.apply(
                lambda row: any(product_id in row[['product_1', 'product_2', 'product_3']].values for product_id in selected_product_ids), axis=1
            )
        ]

        cooccurrence_df = cooccurrence_df.sort_values(by='frequency', ascending=False).reset_index(drop=True)
    else:
        st.warning("No product combinations found. Please check your data.")
        return

    # Now map the product IDs in the product combinations to product names
    for col in cooccurrence_df.columns[1:]:
        cooccurrence_df[col] = cooccurrence_df[col].map(lambda product_id: product_name_map.get(product_id, product_id))

    # Display the results
    if selected_product_sidebar:
        st.subheader(f"Affinity Transactions for {', '.join(selected_product_sidebar)}")
    else:
        st.subheader("All Frequently Bought Product Combinations")

    st.write(cooccurrence_df)
