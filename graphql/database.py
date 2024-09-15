from pymongo import MongoClient
import configparser

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read("config.ini")

# Read MongoDB configurations
DB_URI = config['mongodb']['MONGO_URI']
DB_NAME = config['mongodb']['DB_NAME']
OVERALL_STATS_COLLECTION_NAME = config['mongodb']['OVERALL_STATS_COLLECTION_NAME']
OVERALL_REFERENCE_COLLECTION_NAME = config['mongodb']['OVERALL_REFERENCE_STATS_COLLECTION_NAME']
DATA_STATS_COLLECTION_NAME = config['mongodb']['COLLECTION_NAME_DATA']

# MongoDB Client
client = MongoClient(DB_URI)
db = client[DB_NAME]
overall_stats_collection = db[OVERALL_STATS_COLLECTION_NAME]
overall_reference_collection = db[OVERALL_REFERENCE_COLLECTION_NAME]
collection = db[DATA_STATS_COLLECTION_NAME]
