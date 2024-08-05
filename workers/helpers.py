from quantilemetrics import QuantileMetrics

def compute_histogram(sketch, num_splits=30):
    """
    Reads a binary file, deserializes the content, and extracts the PMF.

    Args:
        filename: Path to the binary file.
        num_splits: Number of splits for the PMF (default: 30).

    Returns:
        A tuple containing x-axis values and the PMF.
    """
    if sketch.is_empty():
        return None, None
    xmin = sketch.get_min_value()
    try:
        step = (sketch.get_max_value() - xmin) / num_splits
    except ZeroDivisionError:
        print(f"Error: num_splits should be non-zero for file {filename}")
        return None, None
    if step == 0:
        step = 0.01

    splits = [xmin + (i * step) for i in range(0, num_splits)]
    pmf = sketch.get_pmf(splits)
    x = splits + [sketch.get_max_value()]  # Append max value for x-axis

    return x, pmf


def compute_distance_metrics(stats1, stats2, metric_name):
    """
    Computes distance metrics between two sets of statistics.

    Args:
        stats1: The first set of statistics.
        stats2: The second set of statistics.
        metric_name: The name of the distance metric to use.

    Returns:
        Dictionary of distance metrics.
    """
    def recursive_distance_computation(dict1, dict2, path=[]):
        distance_metrics = {}
        for key, value in dict1.items():
            if key in dict2:
                if isinstance(value, dict) and isinstance(dict2[key], dict):
                    distance_metrics[key] = recursive_distance_computation(value, dict2[key], path + [key])
                elif isinstance(value, kll_floats_sketch) and isinstance(dict2[key], kll_floats_sketch):
                    # Compute distance metric between sketches
                    x1, pmf1 = get_histogram(value)
                    x2, pmf2 = get_histogram(dict2[key])
                    metrics = QuantileMetrics(pmf1, x1, pmf2, x2)
                    dist = getattr(metrics, metric_name)()
                    distance_metrics[key] = dist
                else:
                    print(f"Skipping key {key} at path {'.'.join(path)} due to incompatible types or missing sub-dictionary.")
        return distance_metrics
    return recursive_distance_computation(stats1, stats2)
