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
    gse = GEOparse.get_GEO(filepath=str(input_dir / f"{gse_id}_family.soft.gz"), silent=True)
    # Extract expression data
    for gsm_name, gsm in gse.gsms.items():
        df = gsm.table
        if 'VALUE' in df.columns:
            expression_data.append(df[['ID_REF', 'VALUE']].set_index('ID_REF').rename(columns={'VALUE': gsm_name}))

# Merge all expression data on ID_REF
merged_data = pd.concat(expression_data, axis=1, join='inner')

# Normalize the data
normalized_data = (merged_data - merged_data.mean()) / merged_data.std()

# Remove zero variance genes
normalized_data = normalized_data.loc[normalized_data.var(axis=1) > 0]

print("Data preprocessing complete.")