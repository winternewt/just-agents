import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

# Check if combined_data is not empty
if not combined_data.empty:
    # Perform PCA
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(combined_data.T)

    # Plot PCA
    plt.figure(figsize=(10, 8))
    plt.scatter(pca_result[:, 0], pca_result[:, 1], alpha=0.7)
    plt.title('PCA of Combined Datasets')
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    plt.grid(True)
    plt.savefig('/output/pca_plot.png')
    plt.show()
else:
    print("No data available for PCA plot.")