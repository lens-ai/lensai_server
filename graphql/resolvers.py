from typing import Optional, List
from database import collection, overall_stats_collection, overall_reference_collection
from models import Metric, MetricDistances, Project, DataEntry, MetricData, MetricType, SensorType, Distances, Distance, DistanceValues
import re
from datetime import datetime, timezone, timedelta

def get_metric_stats(project_id: str, metric: str, submetric: Optional[str] = None, reference: Optional[bool] = False) -> Optional[Metric]:
    query = {"project_id": project_id}
    if reference:
        results = overall_reference_collection.find(query).sort("last_updated", -1).limit(1)
    else:
        results = overall_stats_collection.find(query).sort("last_updated", -1).limit(1)
    for result in results:
        for histogram in result['histograms']:
            if histogram['metric'] == metric and (submetric is None or histogram['submetric'] == submetric):
                    return Metric(
                        metric=histogram['metric'],
                        submetric=histogram['submetric'],
                        pmf=histogram['pmf'],
                        x=histogram['x']
                    )
    return None


def get_metric_distances(project_id: str) -> MetricDistances:
    # Fetch all documents for the given project_id
    documents = overall_stats_collection.find({"project_id": project_id})
    
    # Initialize the result
    distances_list = []

    # Process each document
    for document in documents:
        last_updated = document.get('last_updated', None)  # Fetch the timestamp
        distances = document.get('distance', [])

        # Skip this document if timestamp or distances are empty
        if not last_updated or not distances:
            continue

        distance_objects = [
            Distance(
                metric=d['metric'],
                submetric=d.get('submetric', ''),
                distancevalues=DistanceValues(
                    PSI=d['distances'].get('PSI'),
                    Pearson=d['distances'].get('Pearson'),
                    Euclidean=d['distances'].get('Euclidean')
                )
            )
            for d in distances if d['distances']  # Ensure the distances dictionary is not empty
        ]

        # Skip if distance_objects is empty
        if distance_objects:
            distances_list.append(Distances(timestamp=str(last_updated), distance=distance_objects))
    
    # Return the MetricDistances object if distances_list is not empty
    return MetricDistances(project_id=project_id, distances=distances_list) if distances_list else None



def transform_data(doc):
    sensor_data = {}
    for entry in doc["type"]:
        metrictype = entry["metrictype"]
        if doc["sensor_id"] not in sensor_data:
            sensor_data[doc["sensor_id"]] = {"sensorId": doc["sensor_id"], "timestamp": doc["timestamp"], "data": []}
        
        metrics = []
        for metric_entry in entry["data"]:
            data_entries = []
            for url in metric_entry["data"]:
                data_entries.append(DataEntry(timestamp=extract_timestamp_and_convert(url), url=url))
            metrics.append(MetricData(metric=metric_entry["metric"], submetric=metric_entry["submetric"], data=data_entries))
        sensor_data[doc["sensor_id"]]["data"].append(MetricType(metrictype=metrictype, data=metrics))

    return sensor_data

def extract_timestamp_and_convert(url: str) -> str:
    # Regular expression to match the timestamp in the URL
    pattern = r'_(\d+)\.png'
    match = re.search(pattern, url)
    if not match:
        raise ValueError("No timestamp found in the URL")
    timestamp_ms = int(match.group(1))
    # Convert to datetime
    dt = datetime.fromtimestamp(timestamp_ms/1000000, tz=timezone.utc)
    # Format datetime to string
    dt_str = dt.strftime('%Y-%m-%d %H:%M:%S.%f %Z')
    return dt_str

def fetch_project_data(projectName: str, metrictype: Optional[str] = None, metric: Optional[str] = None,
                       submetric: Optional[str] = None, timestamp: Optional[str] = None, sensorId: Optional[str] = None):
    query = {"project_name": projectName}
    if timestamp:
        query["timestamp"] = timestamp
    if sensorId:
        query["sensor_id"] = sensorId

    cursor = collection.find(query)
    projects = {}
    for doc in cursor:
        if doc["project_name"] not in projects:
            projects[doc["project_name"]] = {"projectName": doc["project_name"], "status": doc["status"], "data": []}
        
        sensor_data = transform_data(doc)
        for sensorId, data in sensor_data.items():
            projects[doc["project_name"]]["data"].append(SensorType(**data))
    project_data = projects.get(projectName, None)
    if project_data:
        return Project(**project_data)
    return None


def get_metrics() -> List[str]:
    # Return the list of unique metrics
    return collection.distinct("data.metric")

def get_submetrics(metric: str) -> List[str]:
    # Return the list of unique submetrics for a given metric
    return collection.distinct("data.data.submetric", {"data.metric": metric})
