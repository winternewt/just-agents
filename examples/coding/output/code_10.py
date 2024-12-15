# Inspect the table structure for GSE148911 to identify available columns

gse_id = 'GSE148911'
gse = GEOparse.get_GEO(filepath=str(input_dir / f'{gse_id}_family.soft.gz'), silent=True)

# Get a sample GSM to inspect the table structure
sample_gsm = next(iter(gse.gsms.values()))

# Print available columns in the table
print("Available columns in GSE148911:", sample_gsm.table.columns)