import strawberry
from strawberry.asgi import GraphQL

@strawberry.type
class Project:
    id: int
    project_name: str
    project_description: str

@strawberry.type
class OverallStats:
    project_id: int
    histograms: list[Histogram]

@strawberry.type
class Histogram:
    last_updated: int
    metrics: list[Metric]

@strawberry.type
class Metric:
    metric: str
    submetric: str | None
    pmf: list[float]
    x: list[float]

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
