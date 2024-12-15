import GEOparse

datasets = ['GSE176043', 'GSE41781', 'GSE148911', 'GSE190986', 'GSE144600']

for gse_id in datasets:
    print(f"Downloading {gse_id}...")
    gse = GEOparse.get_GEO(gse_id, destdir='/input')
    print(f"Downloaded {gse_id}")