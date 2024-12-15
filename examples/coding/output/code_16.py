import GEOparse
import pandas as pd
import numpy as np
from pathlib import Path

# Load datasets
input_dir = Path('/input')
datasets = ['GSE176043', 'GSE41781', 'GSE148911', 'GSE190986', 'GSE144600']
expression_data = []

for gse_id in datasets:
    print(f"Processing {gse_id}...")
    gse = GEOparse.get_GEO(geo=gse_id, destdir=str(input_dir), silent=True)
    # Assuming the expression data is in the first GSM
    gsm = list(gse.gsms.values())[0]
    df = gsm.table
    # Check the columns and clean the data
    print(f"Columns in {gse_id}: {df.columns}")
    if 'VALUE' in df.columns:
        df = df[['ID_REF', 'VALUE']]
        df = df.dropna()
        df = df.set_index('ID_REF')
        expression_data.append(df)
    else:
        print(f"Skipping {gse_id} due to missing 'VALUE' column.")

# Combine all datasets
combined_data = pd.concat(expression_data, axis=1, join='inner')
combined_data = combined_data.apply(pd.to_numeric, errors='coerce')
combined_data = combined_data.dropna()

print("Combined data shape:", combined_data.shape)
print("Combined data head:", combined_data.head())