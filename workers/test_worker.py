import bcrypt
from pymongo import MongoClient
from datetime import datetime

# Constants
DB_URI = "mongodb://localhost:27017/"
DB_NAME = "lensai"

# MongoDB Client
client = MongoClient(DB_URI)
db = client[DB_NAME]

# Drop existing collections to start fresh (optional)
db.drop_collection("devices")
db.drop_collection("users")
db.drop_collection("projects")
db.drop_collection("sensors")
db.drop_collection("sensor_stats")

# Create and populate Device collection
devices = [
    {"device_id": "dev001", "device_mac": "00:11:22:33:44:55", "device_description": "Device 1 Description"},
    {"device_id": "dev002", "device_mac": "66:77:88:99:AA:BB", "device_description": "Device 2 Description"},
]
db.devices.insert_many(devices)

# Function to hash a password
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed

def verify_password(stored_password, provided_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)

# Create and populate User collection with hashed passwords
users = [
    {"user_id": "user001", "user_name": "Alice", "user_email": "alice@example.com", "user_contact": "1234567890", "user_organisation": "Org1", "password": hash_password("password1")},
    {"user_id": "user002", "user_name": "Bob", "user_email": "bob@example.com", "user_contact": "0987654321", "user_organisation": "Org2", "password": hash_password("password2")},
]
db.users.insert_many(users)

# Create and populate Project collection
projects = [
    {"project_id": "proj001", "project_name": "Project 1", "project_users": ["user001", "user002"]},
    {"project_id": "proj002", "project_name": "Project 2", "project_users": ["user001"]},
]
db.projects.insert_many(projects)

# Create and populate Sensor collection
sensors = [
    {"sensor_id": "sens001", "device_id": "dev001", "sensor_project": "proj001", "sensor_createddatetime": datetime.now()},
    {"sensor_id": "sens002", "device_id": "dev002", "sensor_project": "proj002", "sensor_createddatetime": datetime.now()},
]
db.sensors.insert_many(sensors)

# Create and populate Sensor Stats collection
sensor_stats = [
    {
        "project_id": "proj001",
        "sensor_id": "sens001",
        "timestamp": "52437783894",
        "type": [
            {
                "metrictype": "imagestats",
                "stats": [
                    {"metric": "brightness", "submetric": "channel_0", "path": "/path/to/brightness_channel_0.bin"},
                    {"metric": "mean", "submetric": "channel_0", "path": "/path/to/mean_channel_0.bin"},
                    {"metric": "sharpness", "submetric": "channel_0", "path": "/path/to/sharpness_channel_0.bin"},
                ],
            },
            {
                "metrictype": "modelstats",
                "stats": [
                    {"metric": "accuracy", "submetric": "0", "path": "/path/to/accuracy_0.bin"},
                    {"metric": "accuracy", "submetric": "1", "path": "/path/to/accuracy_1.bin"},
                ],
            },
            {
                "metrictype": "samples",
                "stats": [
                    {"metric": "randomsampling", "submetric": "", "path": "/path/to/randomsampling.bin"},
                ],
            },
        ],
    }
]
db.sensor_stats.insert_many(sensor_stats)

# Verify password example
stored_user = db.users.find_one({"user_name": "Alice"})
if stored_user and verify_password(stored_user['password'], "password1"):
    print("Password is correct!")
else:
    print("Password is incorrect!")

print("Collections created and populated successfully!")

