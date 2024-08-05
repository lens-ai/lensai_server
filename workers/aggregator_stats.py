import os
import time
import json
from pathlib import Path
from pymongo import MongoClient
from datasketches import kll_floats_sketch
from helpers import compute_histogram
import numpy as np
from scipy.stats import pearsonr

def compute_psi(original_pmf, reference_pmf, num_bins=1000):
    """Compute the Population Stability Index (PSI)"""
    # Create histograms
    orig_hist, _ = np.histogram(original_pmf, bins=num_bins, density=True)
    ref_hist, _ = np.histogram(reference_pmf, bins=num_bins, density=True)

    # Avoid division by zero
    orig_hist = np.clip(orig_hist, 1e-10, None)
    ref_hist = np.clip(ref_hist, 1e-10, None)

    # Compute PSI
    psi_value = np.sum((orig_hist - ref_hist) * np.log(orig_hist / ref_hist))
    return psi_value

def compute_euclidean_distance(original_pmf, reference_pmf):
    """Compute the Euclidean Distance"""
    return np.sqrt(np.sum((original_pmf - reference_pmf) ** 2))

# Load configuration
with open("config.json") as config_file:
    config = json.load(config_file)

# Constants from config
BASE_PATH = Path(config["base_path"])
DB_URI = config["db_uri"]
DB_NAME = config["db_name"]
COLLECTION_NAME = config["collection_name"]
PROJECT_ID = config["project_id"]
OVERALL_STATS_COLLECTION_NAME = "overall_stats"
OVERALL_REFERENCE_STATS_COLLECTION_NAME = "overall_reference_stats"
SLEEP_INTERVAL = 10  # Sleep interval in seconds

# MongoDB Client
client = MongoClient(DB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
overall_stats_collection = db[OVERALL_STATS_COLLECTION_NAME]
overall_reference_stats_collection = db[OVERALL_REFERENCE_STATS_COLLECTION_NAME]

def get_latest_timestamp_per_sensor():
    pipeline = [
        {"$match": {"status": "completed", "aggregated": 0, "sensor_id": {"$ne": "reference"}}},
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id": "$sensor_id",
            "latest_stats": {"$first": "$$ROOT"}
        }}
    ]
    return list(collection.aggregate(pipeline))

def get_latest_reference_data():
    return collection.find_one({"aggregated": 0, "sensor_id": "reference"}, sort=[("timestamp", -1)])

def gather_bin_files(latest_data):
    metrics_files = {}
    for item in latest_data:
        sensor_data = item['latest_stats']
        types = sensor_data['type']

        for t in types:
            stats = t['stats']
            for stat in stats:
                file_name = os.path.basename(stat['path'])
                if file_name.endswith(".bin"):
                    metric, submetric = file_name.split('_', 1) if '_' in file_name else (file_name, "")
                    submetric = submetric.replace(".bin", "")  # Remove the .bin extension
                    path = stat['path']

                    key = (metric, submetric)
                    if key not in metrics_files:
                        metrics_files[key] = []
                    metrics_files[key].append(path)
    return metrics_files

def read_sketch(bin_file_path):
    with open(bin_file_path, 'rb') as f:
        sketch = kll_floats_sketch.deserialize(f.read())
    return sketch

def aggregate_sketches(bin_file_paths):
    hist_sketch = kll_floats_sketch()
    try:
        for bin_file_path in bin_file_paths:
            hist_sketch.merge(read_sketch(bin_file_path))
        if not hist_sketch.is_empty():
            bin_edges, histogram = compute_histogram(hist_sketch)
            return bin_edges, histogram
        return [], []
    except:
        import pdb
        pdb.set_trace()

def insert_stats(collection, overall_data):
    collection.insert_one(overall_data)
    print(f"Inserted overall stats into the {collection.name} collection.")

def update_aggregated_status(sensor_ids):
    collection.update_many(
        {"sensor_id": {"$in": sensor_ids}, "aggregated": 0},
        {"$set": {"aggregated": 1}}
    )

def process_and_insert_overall_stats():
    latest_data = get_latest_timestamp_per_sensor()
    if not latest_data:
        print("No new data to process.")
        return

    # Process regular sensor data
    metrics_files = gather_bin_files(latest_data)
    histograms = []
    for (metric, submetric), paths in metrics_files.items():
        x, pmf = aggregate_sketches(paths)
        if pmf and x:
            histograms.append({
                "metric": metric,
                "submetric": submetric,
                "pmf": pmf,
                "x": x
            })

    overall_data = {
        "project_id": PROJECT_ID,
        "histograms": [
            {
                "last_updated": int(time.time()),  # Current timestamp
                "metrics": histograms
            }
        ]
    }
    insert_stats(overall_stats_collection, overall_data)

    # Update aggregated status for the processed documents
    sensor_ids = [item['_id'] for item in latest_data]
    update_aggregated_status(sensor_ids)

    # Process reference data
    reference_data = get_latest_reference_data()
    if reference_data:
        reference_metrics_files = gather_bin_files([{'latest_stats': reference_data}])
        reference_histograms = []
        for (metric, submetric), paths in reference_metrics_files.items():
            x, pmf = aggregate_sketches(paths)
            if pmf and x:
                reference_histograms.append({
                    "metric": metric,
                    "submetric": submetric,
                    "pmf": pmf,
                    "x": x
                })

        reference_overall_data = {
            "project_id": PROJECT_ID,
            "histograms": [
                {
                    "last_updated": int(time.time()),  # Current timestamp
                    "metrics": reference_histograms
                }
            ]
        }
        insert_stats(overall_reference_stats_collection, reference_overall_data)
        # Update aggregated status for the processed reference document
        update_aggregated_status([reference_data['_id']])
        overall_dist = compute_metrics(overall_data, reference_overall_data)
        import pdb
        pdb.set_trace()


def compute_metrics(original_dict, reference_dict):
    original_metrics = original_dict['histograms'][0]['metrics']
    reference_metrics = reference_dict['histograms'][0]['metrics']

    overall_distance_stats = {
        "project_id": original_dict["project_id"],
        "timestamp": int(time.time()),  # Using the provided timestamp
        "metrics": []
    }

    # Create a dictionary to access reference metrics easily
    reference_metrics_dict = {(metric['metric'], metric['submetric']): metric for metric in reference_metrics}

    for original_metric in original_metrics:
        key = (original_metric['metric'], original_metric['submetric'])
        if key in reference_metrics_dict:
            reference_metric = reference_metrics_dict[key]

            # Extract PMF
            original_pmf = np.array(original_metric['pmf'])
            reference_pmf = np.array(reference_metric['pmf'])

            # Compute PSI
            psi_value = compute_psi(original_pmf, reference_pmf)

            # Compute Pearson correlation coefficient
            pearson_coeff, _ = pearsonr(original_pmf, reference_pmf)

            # Compute Euclidean distance
            euclidean_distance = compute_euclidean_distance(original_pmf, reference_pmf)

            # Store results in the metrics list
            overall_distance_stats['metrics'].append({
                "metric": original_metric['metric'],
                "submetric": original_metric['submetric'],
                "distances": {
                    "PSI": psi_value,
                    "Pearson": pearson_coeff,
                    "Euclidean": euclidean_distance
                }
            })

    return overall_distance_stats

# Continuous job that runs every 10 seconds
if __name__ == "__main__":
    while True:
        process_and_insert_overall_stats()
        time.sleep(SLEEP_INTERVAL)

