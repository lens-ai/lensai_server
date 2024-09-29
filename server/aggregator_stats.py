import os
import time
import configparser
from pathlib import Path
from pymongo import MongoClient
from datasketches import kll_floats_sketch
from helpers import compute_histogram
import numpy as np
from scipy.stats import pearsonr
from quantilemetrics import QuantileMetrics
from logger import setup_logger
import logging

# Set up logging
setup_logger()

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read("config.ini")

# Constants from config
BASE_PATH = Path(config.get('paths', 'BASE_PATH', fallback='/default/path'))
DB_URI = config.get('mongodb', 'MONGO_URI', fallback='mongodb://localhost:27017')
DB_NAME = config.get('mongodb', 'DB_NAME', fallback='lensai')
COLLECTION_NAME = config.get('mongodb', 'COLLECTION_NAME_STATS', fallback='sensor_stats')
OVERALL_STATS_COLLECTION_NAME = config.get('mongodb', 'OVERALL_STATS_COLLECTION_NAME', fallback='overall_stats')
OVERALL_REFERENCE_STATS_COLLECTION_NAME = config.get('mongodb', 'OVERALL_REFERENCE_STATS_COLLECTION_NAME', fallback='reference_stats')
PROJECT_ID = config.get('DEFAULT', 'PROJECT_ID', fallback='default_project_id')
SLEEP_INTERVAL = config.getint('DEFAULT', 'SLEEP_INTERVAL', fallback=10)

# MongoDB Client
try:
    client = MongoClient(DB_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    overall_stats_collection = db[OVERALL_STATS_COLLECTION_NAME]
    overall_reference_stats_collection = db[OVERALL_REFERENCE_STATS_COLLECTION_NAME]
except Exception as e:
    logging.error(f"Error connecting to MongoDB: {e}")
    raise

def compute_psi(original_pmf, reference_pmf, num_bins=1000):
    """Compute the Population Stability Index (PSI)"""
    try:
        # Create histograms
        orig_hist, _ = np.histogram(original_pmf, bins=num_bins, density=True)
        ref_hist, _ = np.histogram(reference_pmf, bins=num_bins, density=True)

        # Avoid division by zero
        orig_hist = np.clip(orig_hist, 1e-10, None)
        ref_hist = np.clip(ref_hist, 1e-10, None)

        # Compute PSI
        psi_value = np.sum((orig_hist - ref_hist) * np.log(orig_hist / ref_hist))
        return psi_value
    except Exception as e:
        logging.error(f"Error computing PSI: {e}")
        return None

def compute_euclidean_distance(original_pmf, reference_pmf):
    """Compute the Euclidean Distance"""
    try:
        return np.sqrt(np.sum((original_pmf - reference_pmf) ** 2))
    except Exception as e:
        logging.error(f"Error computing Euclidean Distance: {e}")
        return None

def get_latest_timestamp_per_sensor():
    """Fetch the latest timestamp per sensor"""
    try:
        pipeline = [
            {"$match": {"status": "completed", "aggregated": 0, "sensor_id": {"$ne": "reference"}}},
            {"$sort": {"timestamp": -1}},
            {"$group": {
                "_id": "$sensor_id",
                "latest_stats": {"$first": "$$ROOT"}
            }}
        ]
        return list(collection.aggregate(pipeline))
    except Exception as e:
        logging.error(f"Error in getting latest timestamp per sensor: {e}")
        return []

def get_latest_reference_data():
    """Fetch the latest reference data"""
    try:
        return collection.find_one({"sensor_id": "reference", "aggregated": 0}, sort=[("timestamp", -1)])
    except Exception as e:
        logging.error(f"Error in getting latest reference data: {e}")
        return None

def get_latest_reference_stats():
    """Fetch the latest reference stats"""
    try:
        return overall_reference_stats_collection.find_one({"sensor_id": "reference"}, sort=[("timestamp", -1)])
    except Exception as e:
        logging.error(f"Error in getting latest reference stats: {e}")
        return None

def gather_bin_files(latest_data):
    """Gather bin files from the latest data"""
    metrics_files = {}
    if latest_data:
        for item in latest_data:
            sensor_data = item.get('latest_stats', {})
            types = sensor_data.get('type', [])
            for t in types:
                stats = t.get('stats', [])
                for stat in stats:
                    file_name = os.path.basename(stat.get('path', ''))
                    if file_name.endswith(".bin") and not file_name.startswith("._"):
                        metric, submetric = file_name.split('_', 1) if '_' in file_name else (file_name, "")
                        metric = metric.replace(".bin", "")
                        submetric = submetric.replace(".bin", "")
                        path = stat.get('path', '')
                        key = (metric, submetric)
                        if key not in metrics_files:
                            metrics_files[key] = []
                        metrics_files[key].append(path)
    return metrics_files

def read_sketch(bin_file_path):
    """Read and deserialize a sketch from a binary file"""
    try:
        with open(bin_file_path, 'rb') as f:
            sketch = kll_floats_sketch.deserialize(f.read())
            return sketch
    except Exception as e:
        logging.error(f"Error reading sketch from {bin_file_path}: {e}")
        return None

def aggregate_sketches(bin_file_paths):
    """Aggregate sketches from multiple bin files"""
    hist_sketch = kll_floats_sketch()
    try:
        for bin_file_path in bin_file_paths:
            sketch = read_sketch(bin_file_path)
            if sketch:
                hist_sketch.merge(sketch)
        if not hist_sketch.is_empty():
            bin_edges, histogram = compute_histogram(hist_sketch)
            return bin_edges, histogram
        return [], []
    except Exception as e:
        logging.error(f"Error aggregating sketches: {e}")
        return [], []

def insert_stats(collection, overall_data):
    """Insert overall stats into the specified MongoDB collection"""
    try:
        collection.insert_one(overall_data)
        logging.info(f"Inserted overall stats into the {collection.name} collection.")
    except Exception as e:
        logging.error(f"Error inserting stats into {collection.name}: {e}")

def update_aggregated_status(sensor_ids):
    """Update aggregated status for given sensor IDs"""
    try:
        collection.update_many(
            {"sensor_id": {"$in": sensor_ids}, "aggregated": 0},
            {"$set": {"aggregated": 1}}
        )
        logging.info(f"Updated aggregated status for sensor IDs: {sensor_ids}")
    except Exception as e:
        logging.error(f"Error updating aggregated status: {e}")

def process_and_insert_overall_stats():
    """Main function to process and insert overall stats"""
    latest_data = get_latest_timestamp_per_sensor()
    if not latest_data:
        logging.info("No new data to process.")
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
        reference_stats = {
            "project_id": PROJECT_ID,
            "last_updated": int(time.time()),
            "histograms": reference_histograms
        }
        insert_stats(overall_reference_stats_collection, reference_stats) 
        update_aggregated_status([reference_data['_id']])
    else:
        reference_stats = get_latest_reference_stats()

    if not reference_stats:
        logging.error("Reference Stats Empty, Please publish reference stats")

    dist = compute_metrics(histograms, reference_stats)
    overall_data = {
        "project_id": PROJECT_ID,
        "last_updated": int(time.time()),
        "histograms": histograms,
        "distance": dist 
    }
    insert_stats(overall_stats_collection, overall_data)
    
    sensor_ids = [item['_id'] for item in latest_data]
    update_aggregated_status(sensor_ids)

def compute_metrics(original_list, reference_dict):
    """Compute various metrics comparing original data to reference data"""
    original_metrics = original_list
    reference_metrics = reference_dict.get('histograms', [])

    overall_distance_stats = []
    reference_metrics_dict = {(metric['metric'], metric['submetric']): metric for metric in reference_metrics}
    for original_metric in original_metrics:
        key = (original_metric['metric'], original_metric['submetric'])
        if key in reference_metrics_dict:
            reference_metric = reference_metrics_dict[key]
            original_pmf = np.array(original_metric['pmf'])
            reference_pmf = np.array(reference_metric['pmf'])

            metrics = QuantileMetrics(original_metric['pmf'], original_metric['x'],
                                      reference_metric['pmf'], reference_metric['x'])
            psi_value = getattr(metrics, "psi")()
            pearson_coeff = getattr(metrics, "pearson_correlation")()
            euclidean_distance = getattr(metrics, "euclidean_distance")()

            overall_distance_stats.append({
                "metric": original_metric['metric'],
                "submetric": original_metric['submetric'],
                "distances": {
                    "PSI": psi_value,
                    "Pearson": pearson_coeff,
                    "Euclidean": euclidean_distance
                }
            })

    return overall_distance_stats

# Continuous job that runs every SLEEP_INTERVAL seconds
if __name__ == "__main__":
    while True:
        process_and_insert_overall_stats()
        time.sleep(SLEEP_INTERVAL)

