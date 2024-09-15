import os
import time
import tarfile
import configparser
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# server.py (or any other script)
from logger import setup_logger
import logging

# Set up logging
setup_logger()

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Constants from config
BASE_PATH = Path(config['paths']['BASE_PATH'])
DB_URI = config['mongodb']['MONGO_URI']
DB_NAME = config['mongodb']['DB_NAME']
COLLECTION_NAME_STATS = config['mongodb']['COLLECTION_NAME_STATS']
COLLECTION_NAME_AGGREGATE = config['mongodb']['COLLECTION_NAME_AGGREGATE']
PROJECT_NAME = config['DEFAULT']['PROJECT_ID']
NUM_WORKERS = int(config['DEFAULT']['NUM_WORKERS'])

# MongoDB Client
client = MongoClient(DB_URI)
db = client[DB_NAME]
collection_stats = db[COLLECTION_NAME_STATS]
collection_aggregate = db[COLLECTION_NAME_AGGREGATE]

# Function to extract tar.gz without root folder
def extract_tar_without_root(tar_path, extract_path):
    """Extracts tar.gz file without creating a root directory."""
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=extract_path)
        logging.info(f"Extracted {tar_path} to {extract_path}")
    except (tarfile.TarError, IOError) as e:
        logging.error(f"Error extracting {tar_path}: {e}")

# Function to process and insert data into MongoDB
def process_and_insert_data(sensor_id, timestamp, dir_path):
    """
    Process tar.gz data for a specific sensor and timestamp, 
    and insert or update MongoDB documents.
    """
    # Prepare the initial data
    data = {
        "project_name": PROJECT_NAME,
        "sensor_id": sensor_id,
        "timestamp": timestamp,
        "status": "processing",
        "aggregated": 0,
        "type": []
    }

    # Insert or update the document in the stats collection
    try:
        collection_stats.update_one(
            {"sensor_id": sensor_id, "timestamp": timestamp},
            {"$setOnInsert": data},
            upsert=True
        )
    except DuplicateKeyError:
        logging.info(f"Document already exists for sensor_id: {sensor_id}, timestamp: {timestamp}")
        return

    # Extract tar.gz file if it exists
    tar_path = os.path.join(dir_path, "stats.tar.gz")
    if os.path.exists(tar_path):
        extract_tar_without_root(tar_path, dir_path)
        os.remove(tar_path)  # Clean up the tar.gz file

    # Process extracted data and update MongoDB
    processed_data = {"type": [], "status": "completed"}
    for metrictype in ["imgstats", "modelstats", "samples", "customstats"]:
        metrictype_path = os.path.join(dir_path, metrictype)
        if os.path.exists(metrictype_path):
            stats = []
            for file_name in os.listdir(metrictype_path):
                if file_name.endswith(".bin"):
                    metric, submetric = file_name.split('_', 1) if '_' in file_name else (file_name, "")
                    metric = metric.replace(".bin", "")
                    submetric = submetric.replace(".bin", "")
                    stats.append({
                        "metric": metric,
                        "submetric": submetric,
                        "path": os.path.join(metrictype_path, file_name)
                    })
            if stats:
                processed_data["type"].append({
                    "metrictype": metrictype,
                    "stats": stats
                })

    # Update the document with the processed data
    try:
        collection_stats.update_one(
            {"sensor_id": sensor_id, "timestamp": timestamp},
            {"$set": processed_data}
        )
        logging.info(f"Data processed for sensor_id: {sensor_id}, timestamp: {timestamp}")

        # Update the aggregation status
        collection_aggregate.update_one(
            {"sensor_id": sensor_id, "timestamp": timestamp},
            {"$set": {"extracted": 1}}
        )
    except Exception as e:
        logging.error(f"Error updating document for sensor_id: {sensor_id}, timestamp: {timestamp}: {e}")

# Function to continuously check and process unextracted documents
def check_and_process_unextracted_docs(executor):
    """Continuously checks for unextracted documents and processes them."""
    while True:
        try:
            # Find unextracted documents
            unextracted_docs = collection_aggregate.find({"extracted": 0, "file_type": "stats"})
            for doc in unextracted_docs:
                sensor_id = doc["sensor_id"]
                timestamp = doc["timestamp"]
                dir_path = doc["path"]
                executor.submit(process_and_insert_data, sensor_id, timestamp, dir_path)
        except Exception as e:
            logging.error(f"Error processing unextracted documents: {e}")
        time.sleep(10)  # Poll every 10 seconds

if __name__ == "__main__":
    # Setup Thread Pool for parallel processing
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        # Start checking and processing unextracted documents
        check_and_process_unextracted_docs(executor)

