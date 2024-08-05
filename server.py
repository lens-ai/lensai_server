from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import os
import shutil
import logging
from pymongo import MongoClient, errors

app = FastAPI()

# Define the base path for storing the files
BASE_PATH = Path("/tmp")  # Change this to your desired base directory

# Set up logging
logging.basicConfig(level=logging.INFO)

client = MongoClient("mongodb://localhost:27017/")
db = client["lensai"]
collection = db["to_aggregate"]

# Create unique index on sensor_id and timestamp
collection.create_index([("sensor_id", 1), ("timestamp", 1)], unique=True)


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
    
    except errors.DuplicateKeyError:
        logging.error("Duplicate entry found for sensor_id: %s, timestamp: %s", sensor_id, timestamp)
        return JSONResponse(content={"message": "Duplicate entry"}, status_code=400)
    except Exception as e:
        logging.error("Error uploading file: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
