from fastapi import FastAPI
from typing import List
from pymongo import MongoClient
import strawberry
from strawberry.asgi import GraphQL
from datetime import datetime

app = FastAPI()

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["lensai"]

@strawberry.type
class Project:
    id_: str
    name: str

@strawberry.type
class Metric:
    metric: str
    submetric: str
    pmf: list[float]
    x: list[float]


@strawberry.type
class Histogram:
    last_updated: int
    metrics: list[Metric]


@strawberry.type
class OverallStats:
    project_id: str
    histograms: list[Histogram]


@strawberry.type
class Sensor:
    sensor_id: int
    device_id: str
    sensor_project: str
    sensor_created_datetime: datetime

@strawberry.type
class Device:
    device_id: int
    device_mac: str
    device_description: str
@strawberry.type


class Query:
    @strawberry.field
    def projects(self) -> List[Project]:
        projects = []
        collection = db['projects']
        for project_data in collection.find():
            project = Project(id_=project_data["project_id"], name=project_data["project_name"])
            projects.append(project)
        return projects

    @strawberry.field
    def project(self, id_: str) -> Project:
        collection = db['projects']
        project_data = collection.find_one({"project_id": id_})
        if project_data:
            return Project(id_=project_data["project_id"], name=project_data["project_name"])
        else:
            return None

    @strawberry.field
    def overallstats(self, id: str) -> OverallStats:
        collection = db['overall_stats']
        stats_data = collection.find_one({"project_id": id})
        if stats_data:
            return stats_data
        else:
            return None



schema = strawberry.Schema(query=Query)
app.mount("/graphql", GraphQL(schema, debug=True))
