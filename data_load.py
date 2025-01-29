import os
import pandas as pd

# Path to the directory containing the CSV files
directory_path = 'data/'

# List to hold individual dataframes
df_list = []

# Loop through each file in the directory
for filename in os.listdir(directory_path):
    if filename.endswith('.csv'):  # Check if the file is a CSV
        file_path = os.path.join(directory_path, filename)
        # Read the CSV and append to the list
        df = pd.read_csv(file_path)
        df_list.append(df)

# Concatenate all dataframes into one
combined_df = pd.concat(df_list, ignore_index=True)

# Display the combined dataframe
print(combined_df)
