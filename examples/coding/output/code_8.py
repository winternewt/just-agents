import pandas as pd
import numpy as np
from pathlib import Path
import GEOparse

# Load datasets
input_dir = Path('/input')
gse_ids = ['GSE176043', 'GSE41781', 'GSE148911', 'GSE190986', 'GSE144600']

# Function to preprocess each dataset
# Normalize and remove zero variance genes
def preprocess_gse(gse_id):
    gse = GEOparse.get_GEO(filepath=input_dir / f'{gse_id}_family.soft.gz', silent=True)
    # Extract expression data
    samples = gse.gsms
    data = pd.DataFrame({gsm: samples[gsm].table['VALUE'] for gsm in samples})
    data.index = samples[next(iter(samples))].table['ID_REF']
    # Remove zero variance genes
    data = data.loc[data.var(axis=1) > 0]
    # Normalize data
    data = (data - data.mean()) / data.std()
    return data

# Preprocess and combine datasets
combined_data = pd.DataFrame()
for gse_id in gse_ids:
    print(f"Preprocessing {gse_id}...")
    data = preprocess_gse(gse_id)
    combined_data = pd.concat([combined_data, data], axis=1, join='inner')
    print(f"Processed {gse_id}")

print("Combined data shape:", combined_data.shape)