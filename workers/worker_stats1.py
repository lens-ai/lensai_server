import os
import time
import tarfile
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pymongo import MongoClient

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

# Function to extract tar.gz without root folder
def extract_tar_without_root(tar_path, extract_path):
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            member_path = Path(member.name)
            # Ignore the root folder by stripping the first part
            if member_path.parts:
                member.name = str(Path(*member_path.parts[1:]))
                tar.extract(member, path=extract_path)

# Function to process and insert data into MongoDB
def process_and_insert_data(sensor_id, timestamp):
    folder_path = os.path.join(BASE_PATH, "lensai", "stats", sensor_id, str(timestamp))

    # Extract tar.gz file
    tar_path = os.path.join(folder_path, "stats.tgz")
    if os.path.exists(tar_path):
        extract_tar_without_root(tar_path, folder_path)
        os.remove(tar_path)  # Delete the tar.gz file after extraction

    # Check if a document with the same sensor_id and timestamp exists
    existing_document = collection.find_one({"sensor_id": sensor_id, "timestamp": timestamp})
    if existing_document:
        print(f"Document already exists for sensor_id: {sensor_id}, timestamp: {timestamp}")
        return

    data = {
        "project_name": PROJECT_NAME,  # Use project_id from config
        "sensor_id": sensor_id,
        "timestamp": timestamp,
        "type": []
    }

    for metrictype in ["imgstats", "modelstats", "samples", "customstats"]:
        metrictype_path = os.path.join(folder_path, metrictype)
        if os.path.exists(metrictype_path):
            stats = []
            for file_name in os.listdir(metrictype_path):
                if file_name.endswith(".bin"):
                    metric, submetric = file_name.split('_', 1) if '_' in file_name else (file_name, "")
                    stats.append({
                        "metric": metric,
                        "submetric": submetric,
                        "path": os.path.join(metrictype_path, file_name)
                    })
            if stats:
                data["type"].append({
                    "metrictype": metrictype,
                    "stats": stats
                })

    collection.insert_one(data)
    try:
        # Find and delete the document
        result = collection_aggregate.delete_one({"sensor_id": sensor_id, "timestamp": timestamp})
        if result.deleted_count == 1:
            logging.info("Document deleted for sensor_id: %s, timestamp: %s", sensor_id, timestamp)
            return JSONResponse(content={"message": "Document deleted successfully"}, status_code=200)
        else:
            logging.warning("No document found for sensor_id: %s, timestamp: %s", sensor_id, timestamp)
            return JSONResponse(content={"message": "Document not found"}, status_code=404)

    except Exception as e:
        logging.error("Error deleting document: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

    print(f"Inserted data for sensor_id: {sensor_id}, timestamp: {timestamp}")


# Event Handler
class StatsHandler(FileSystemEventHandler):
    def __init__(self, executor):
        self.executor = executor

    def on_created(self, event):
        # Check if the event is a file creation and it's a tar.gz file
        if not event.is_directory:
            tar_path = Path(event.src_path)
            sensor_id = tar_path.parent.parent.name
            timestamp = tar_path.parent.name
            self.executor.submit(process_and_insert_data, sensor_id, timestamp)

def initial_scan(base_path, executor):
    for sensor_id_dir in (base_path / "lensai" / "stats").iterdir():
        if sensor_id_dir.is_dir():
            for timestamp_dir in sensor_id_dir.iterdir():
                if timestamp_dir.is_dir():
                    tar_path = timestamp_dir / "stats.tgz"
                    sensor_id = sensor_id_dir.name
                    timestamp = timestamp_dir.name
                    executor.submit(process_and_insert_data, sensor_id, timestamp)


# Setup Observer and Thread Pool
executor = ThreadPoolExecutor(max_workers=NUM_WORKERS)
event_handler = StatsHandler(executor)
observer = Observer()
observer.schedule(event_handler, BASE_PATH / "lensai" / "stats", recursive=True)

# Initial scan of existing directories
initial_scan(BASE_PATH, executor)

# Start observer
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
    executor.shutdown(wait=True)

observer.join()

