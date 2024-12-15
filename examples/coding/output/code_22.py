import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import pandas as pd

# Perform PCA
pca = PCA(n_components=2)
pca_result = pca.fit_transform(normalized_data.T)

# Create a DataFrame for PCA results
pca_df = pd.DataFrame(data=pca_result, columns=['PC1', 'PC2'])

# Plot PCA
plt.figure(figsize=(10, 8))
plt.scatter(pca_df['PC1'], pca_df['PC2'], alpha=0.5)
plt.title('PCA of Combined GEO Datasets')
plt.xlabel('Principal Component 1')
plt.ylabel('Principal Component 2')
plt.grid(True)

# Save the plot
output_path = '/output/pca_plot.png'
plt.savefig(output_path)
plt.close()

print(f"PCA plot saved to {output_path}.")