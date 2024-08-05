from pydantic import BaseModel, Field as PydanticField
from datetime import datetime

class ProjectModel(BaseModel):
    id: int = PydanticField(..., alias='_id')
    project_id: str
    project_name: str

class HistogramModel(BaseModel):
    last_updated: int
    metrics: list

class MetricModel(BaseModel):
    metric: str
    submetric: str = None
    pmf: list
    x: list

class OverallStatsModel(BaseModel):
    project_id: str
    histograms: list

class SensorModel(BaseModel):
    sensor_id: int
    device_id: str
    sensor_project: str
    sensor_created_datetime: datetime

class DeviceModel(BaseModel):
    device_id: int
    device_mac: str
    device_description: str
