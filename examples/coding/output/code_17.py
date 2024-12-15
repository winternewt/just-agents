# Re-evaluate the approach by checking the available columns in the problematic datasets
import GEOparse

# Function to inspect the columns of each dataset

def inspect_dataset_columns(gse_id):
    gse = GEOparse.get_GEO(geo=gse_id, destdir='/input', silent=True)
    for gsm_name, gsm in gse.gsms.items():
        print(f"GSM: {gsm_name}, Columns: {gsm.table.columns}")
        break  # Only inspect the first GSM for simplicity

# Inspect the problematic datasets
problematic_datasets = ['GSE148911', 'GSE190986', 'GSE144600']

for gse_id in problematic_datasets:
    print(f"Inspecting {gse_id}...")
    inspect_dataset_columns(gse_id)