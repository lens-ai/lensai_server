import os
import time
import tarfile
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from pymongo import MongoClient
import logging

# Load configuration
with open("config.json") as config_file:
    config = json.load(config_file)

# Constants from config
BASE_PATH = Path(config["base_path"])
DB_URI = config["db_uri"]
DB_NAME = config["db_name"]
COLLECTION_NAME = config["collection_name"]
PROJECT_NAME = config["project_id"]
NUM_WORKERS = config["num_workers"]

# MongoDB Client
client = MongoClient(DB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
collection_aggregate = db["to_aggregate"]

# Set up logging
logging.basicConfig(level=logging.INFO)

# Function to extract tar.gz without root folder
def extract_tar_without_root(tar_path, extract_path):
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            tar.extract(member, path=extract_path)

# Function to process and insert data into MongoDB
def process_and_insert_data(sensor_id, timestamp, dir_path):
    # Prepare the initial data
    data = {
        "project_name": PROJECT_NAME,
        "sensor_id": sensor_id,
        "timestamp": timestamp,
        "status": "processing",
        "aggregated": 0,
        "type": []
    }

    # Insert the initial document or find existing one
    try:
        collection.update_one(
            {"sensor_id": sensor_id, "timestamp": timestamp},
            {"$setOnInsert": data},
            upsert=True
        )
    except DuplicateKeyError:
        # Document already exists, no further action needed here
        logging.info(f"Document already exists for sensor_id: {sensor_id}, timestamp: {timestamp}")
        return

    # Extract tar.gz file and process data
    tar_path = os.path.join(dir_path, "stats.tar.gz")
    if os.path.exists(tar_path):
        extract_tar_without_root(tar_path, dir_path)
        os.remove(tar_path)  # Delete the tar.gz file after extraction

    # Gather processed data
    processed_data = {
        "type": [],
        "status": "completed"
    }
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

    # Update the document with processed data and set status to "completed"
    collection.update_one(
        {"sensor_id": sensor_id, "timestamp": timestamp},
        {"$set": processed_data}
    )
    logging.info(f"Data processed and updated for sensor_id: {sensor_id}, timestamp: {timestamp}")
    collection_aggregate.update_one(
        {"sensor_id": sensor_id, "timestamp": timestamp},
        {"$set": {"extracted": 1}}
    )

# Function to check and process unextracted documents
def check_and_process_unextracted_docs(executor):
    while True:
        unextracted_docs = collection_aggregate.find({"extracted": 0, "file_type":"stats"})
        for doc in unextracted_docs:
            sensor_id = doc["sensor_id"]
            timestamp = doc["timestamp"]
            dir_path = doc["path"]
            executor.submit(process_and_insert_data, sensor_id, timestamp, dir_path)
        time.sleep(10)  # Wait before checking again

# Setup Thread Pool
executor = ThreadPoolExecutor(max_workers=NUM_WORKERS)

# Start checking and processing unextracted documents
check_and_process_unextracted_docs(executor)

