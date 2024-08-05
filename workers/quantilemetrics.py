import numpy as np
from scipy.spatial import distance
from scipy.stats import pearsonr, spearmanr, entropy, wasserstein_distance
from scipy.spatial.distance import jensenshannon
from scipy.interpolate import interp1d

class QuantileMetrics:

    def __init__(self, hist1, bins1, hist2, bins2):
        """
        Initialize the class with two histograms and their respective bin edges.
        hist1, hist2: Arrays representing the histogram counts.
        bins1, bins2: Arrays representing the bin edges.
        """
        self.hist1 = np.array(hist1)
        self.hist2 = np.array(hist2)
        self.bins1 = self.normalize_bins(np.array(bins1), min(bins1), max(bins1))
        self.bins2 = self.normalize_bins(np.array(bins2), min(bins2), max(bins2))

        # Create common bins
        self.common_bins = np.union1d(self.bins1, self.bins2)

        # Rebin the histograms to the common bins
        self.rebinned_hist1 = self.rebin_histogram(self.hist1, self.bins1, self.common_bins)
        self.rebinned_hist2 = self.rebin_histogram(self.hist2, self.bins2, self.common_bins)

    def rebin_histogram(self, hist, original_bins, common_bins):
        """
        Rebin the histogram to a common set of bins.
        """
        # Create an empty array for the new bins
        rebinned = np.zeros(len(common_bins) - 1, dtype=float)

        # Fill the new bins with appropriate counts
        for i in range(len(original_bins) - 1):
            # Find the indices where the original bins fall into the common bins
            start = np.searchsorted(common_bins, original_bins[i], side='right') - 1
            end = np.searchsorted(common_bins, original_bins[i + 1], side='left')

            # Distribute the count across the corresponding new bins
            if start < end:
                rebinned[start:end] += hist[i]

        return rebinned

    
    def normalize_bins(self, x, min_val, max_val):
        return (x - min_val) / (max_val - min_val)
    
    def euclidean_distance(self):
        """
        Compute the Euclidean distance.
        """
        return distance.euclidean(self.rebinned_hist1, self.rebinned_hist2)

    def manhattan_distance(self):
        """
        Compute the Manhattan distance.
        """
        return distance.cityblock(self.rebinned_hist1, self.rebinned_hist2)

    def cosine_similarity(self):
        """
        Compute the cosine similarity.
        """
        return 1 - distance.cosine(self.rebinned_hist1, self.rebinned_hist2)

    def pearson_correlation(self):
        """
        Compute the Pearson correlation coefficient.
        """
        return pearsonr(self.rebinned_hist1, self.rebinned_hist2)[0]

    def spearman_rank_correlation(self):
        """
        Compute the Spearman rank correlation coefficient.
        """
        return spearmanr(self.rebinned_hist1, self.rebinned_hist2)[0]

    def jensen_shannon_divergence(self):
        """
        Compute the Jensen-Shannon divergence.
        """
        return jensenshannon(self.rebinned_hist1, self.rebinned_hist2)

    def kullback_leibler_divergence(self):
        """
        Compute the Kullback-Leibler divergence.
        """
        return entropy(self.rebinned_hist1, self.rebinned_hist2)

    def hellinger_distance(self):
        """
        Compute the Hellinger distance.
        """
        return np.sqrt(np.sum((np.sqrt(self.rebinned_hist1) - np.sqrt(self.rebinned_hist2)) ** 2)) / np.sqrt(2)

    def wasserstein_distance(self):
        """
        Compute the Wasserstein distance.
        """
        return wasserstein_distance(self.rebinned_hist1, self.rebinned_hist2)

    def psi(self, num_buckets=10):
        """
        Calculate the Population Stability Index (PSI) between two distributions.

        Args:
            expected_x (array-like): The x values of the expected distribution.
            expected_pmf (array-like): The PMF values of the expected distribution.
            actual_x (array-like): The x values of the actual distribution.
            actual_pmf (array-like): The PMF values of the actual distribution.
            num_buckets (int): Number of buckets to split the distributions into.

        Returns:
            float: The PSI value.
        """
        # Interpolate PMFs to a common x range
        min_x = max(min(self.bins1), min(self.bins2))
        max_x = min(max(self.bins1), max(self.bins2))
        common_x = np.linspace(min_x, max_x, num_buckets + 1)
    
        interp_expected = interp1d(self.bins1, self.hist1, kind='linear', fill_value="extrapolate")
        interp_actual = interp1d(self.bins2, self.hist2, kind='linear', fill_value="extrapolate")
    
        common_expected_pmf = interp_expected(common_x)
        common_actual_pmf = interp_actual(common_x)
    
        # Ensure no zero values for log and division calculations
        common_expected_pmf = np.where(common_expected_pmf == 0, 0.0001, common_expected_pmf)
        common_actual_pmf = np.where(common_actual_pmf == 0, 0.0001, common_actual_pmf)
    
        # Calculate the PSI
        psi_value = np.sum((common_expected_pmf - common_actual_pmf) * np.log(common_expected_pmf / common_actual_pmf))
    
        return psi_value

        
    @staticmethod
    def available_metrics():
        return [
            "euclidean_distance",
            "manhattan_distance",
            "cosine_similarity",
            "pearson_correlation",
            "spearman_rank_correlation",
            "jensen_shannon_divergence",
            "kullback_leibler_divergence",
            "hellinger_distance",
            "wasserstein_distance",
            "psi"
        ]
