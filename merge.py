import os
import pandas as pd

# --- Configuration ---
input_folder = r'C:\Users\it\Documents\unified_app\stockr' 
output_file = 'merged_output.csv'

# --- Get list of CSV files in the folder ---
csv_files = [file for file in os.listdir(input_folder) if file.endswith('.csv')]

# --- Read and concatenate all CSVs ---
merged_df = pd.concat(
    [pd.read_csv(os.path.join(input_folder, file)) for file in csv_files],
    ignore_index=True
)


# --- Export to CSV ---
merged_df.to_csv(output_file, index=False)
print(f"✅ Merged {len(csv_files)} files into '{output_file}'")
