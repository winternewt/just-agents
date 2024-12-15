import GEOparse

gse_ids = ['GSE176043', 'GSE41781', 'GSE148911', 'GSE190986', 'GSE144600']

for gse_id in gse_ids:
    print(f"Downloading {gse_id}...")
    gse = GEOparse.get_GEO(geo=gse_id, destdir='/input', silent=True)
    print(f"Downloaded {gse_id}")