from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from pathlib import Path
import os
import shutil
from pymongo import MongoClient, errors
import configparser

# server.py (or any other script)
from logger import setup_logger
import logging

# Set up logging
setup_logger()

# Load configurations
config = configparser.ConfigParser()
config.read('config.ini')

# Read from config file
BASE_PATH = Path(config['paths']['BASE_PATH'])
MONGO_URI = config['mongodb']['MONGO_URI']
DB_NAME = config['mongodb']['DB_NAME']
COLLECTION_NAME = config['mongodb']['COLLECTION_NAME_AGGREGATE']

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize MongoDB client
try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Check if the index already exists
    existing_indexes = collection.index_information()
    if 'sensor_id_1_timestamp_1' not in existing_indexes:
        try:
            collection.create_index([("sensor_id", 1), ("timestamp", 1)], unique=True)
            logging.info("Index on sensor_id and timestamp created successfully.")
        except errors.DuplicateKeyError as e:
            logging.error(f"Duplicate key error while creating index: {e}")
    else:
        logging.info("Index on sensor_id and timestamp already exists.")

except errors.ConnectionFailure as e:
    logging.error(f"Could not connect to MongoDB: {e}")
    raise Exception("Could not connect to MongoDB")

app = FastAPI()

@app.post("/upload/")
async def upload_file(
    sensor_id: str = Form(...),
    timestamp: str = Form(...),
    file_type: str = Form(...),
    file: UploadFile = File(...)
):
    # Validate file_type
    if file_type not in ["stats", "data"]:
        logging.error("Invalid file type provided: %s", file_type)
        raise HTTPException(status_code=400, detail="Invalid file type. Must be 'stats' or 'data'.")

    try:
        # Construct the directory path under lensai
        dir_path = BASE_PATH / "lensai" / file_type / sensor_id / timestamp
        
        # Create the directory if it doesn't exist
        dir_path.mkdir(parents=True, exist_ok=True)

        # Construct the file path
        file_path = dir_path / "{}.tar.gz".format(file_type)

        # Save the file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Check if a document with the same sensor_id and timestamp exists
        existing_document = collection.find_one({"sensor_id": sensor_id, "timestamp": timestamp})
        if existing_document:
            logging.info("Document already exists for sensor_id: %s, timestamp: %s", sensor_id, timestamp)
            return JSONResponse(content={"message": "Document already exists"}, status_code=200)

        # Insert document into MongoDB
        data = {
            'sensor_id': sensor_id,
            'timestamp': timestamp,
            'path': str(dir_path),
            'file_type': file_type,
            'extracted': 0
        }
        collection.insert_one(data)
        logging.info("File uploaded and document inserted successfully: %s", file_path)

        return JSONResponse(content={"message": "File uploaded successfully"}, status_code=201)
    
    except errors.DuplicateKeyError as e:
        logging.error("Duplicate entry for sensor_id: %s, timestamp: %s. Error: %s", sensor_id, timestamp, e)
        return JSONResponse(content={"message": "Duplicate entry found, document already exists"}, status_code=200)
    except OSError as e:
        logging.error("File system error: %s", e)
        raise HTTPException(status_code=500, detail="File system error")
    except Exception as e:
        logging.error("Error uploading file: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

