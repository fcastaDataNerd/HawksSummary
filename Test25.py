import os
import pandas as pd

# Set input and output folders
input_folder = "C:/Users/franc/OneDrive/NECBLHISTORY/Test2025"
output_folder_1 = "C:/Users/franc/OneDrive/NECBLHISTORY/Test2025/Master"
output_folder_2 = "C:/Users/franc/OneDrive/Hawks25/HawksDaily"

# Output file names
output_file_1 = os.path.join(output_folder_1, "Test2025_combined.csv")
output_file_2 = os.path.join(output_folder_2, "Test2025_combined.csv")

# Ensure both output folders exist
os.makedirs(output_folder_1, exist_ok=True)
os.makedirs(output_folder_2, exist_ok=True)

# Get all CSV files in the input folder
csv_files = [file for file in os.listdir(input_folder) if file.endswith(".csv")]

# Collect all DataFrames
dfs = []

for file in csv_files:
    file_path = os.path.join(input_folder, file)
    try:
        df = pd.read_csv(file_path)
        df["Source"] = file  # Optional metadata
        dfs.append(df)
    except Exception as e:
        print(f"Error reading {file}: {e}")

# Combine and save to both outputs
if dfs:
    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df.to_csv(output_file_1, index=False)
    combined_df.to_csv(output_file_2, index=False)
    print(f"✅ Combined CSV written to:\n - {output_file_1}\n - {output_file_2}")
else:
    print("⚠️ No CSV files found in the folder.")
