import strawberry
from strawberry.types import Info
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
import models
from datetime import datetime

# MongoDB client
client = AsyncIOMotorClient('mongodb://localhost:27017')
db = client['lensai']

# Define the Strawberry types
@strawberry.type
class MetricType:
    metric: str
    submetric: Optional[str]
    pmf: List[float]
    x: List[float]

@strawberry.type
class HistogramType:
    last_updated: int
    metrics: List[MetricType]

@strawberry.type
class OverallStatsType:
    project_id: str
    histograms: List[HistogramType]

@strawberry.type
class ProjectType:
    id: int
    project_id: str
    project_name: str

@strawberry.type
class SensorType:
    sensor_id: int
    device_id: str
    sensor_project: str
    sensor_created_datetime: datetime

@strawberry.type
class DeviceType:
    device_id: int
    device_mac: str
    device_description: str

# Define the Queries
@strawberry.type
class Query:
    @strawberry.field
    async def all_projects(self) -> List[ProjectType]:
        projects = await db['projects'].find().to_list(100)
        return [ProjectType(**project) for project in projects]

    @strawberry.field
    async def all_overall_stats(self, project_id: Optional[str] = None) -> List[OverallStatsType]:
        query = {}
        if project_id:
            query['project_id'] = project_id
        overall_stats = await db['overall_stats'].find(query).to_list(100)
        return [OverallStatsType(**stat) for stat in overall_stats]

    @strawberry.field
    async def all_sensors(self) -> List[SensorType]:
        sensors = await db['sensors'].find().to_list(100)
        return [SensorType(**sensor) for sensor in sensors]

    @strawberry.field
    async def all_devices(self) -> List[DeviceType]:
        devices = await db['devices'].find().to_list(100)
        return [DeviceType(**device) for device in devices]

# Define the Mutations
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_project(self, project_id: str, project_name: str) -> ProjectType:
        project_data = {
            "project_id": project_id,
            "project_name": project_name
        }
        result = await db['projects'].insert_one(project_data)
        project_data['id'] = result.inserted_id
        return ProjectType(**project_data)

# Create the schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

