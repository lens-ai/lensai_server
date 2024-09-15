import strawberry
from typing import List, Optional

@strawberry.type
class Metric:
    metric: str
    submetric: Optional[str]
    pmf: List[float]
    x: List[float]

@strawberry.type
class DistanceValues:
    PSI: Optional[float]
    Pearson: Optional[float]
    Euclidean: Optional[float]

@strawberry.type
class Distance:
    metric: str
    submetric: Optional[str]
    distancevalues: DistanceValues

@strawberry.type
class Distances:
    timestamp: str
    distance: List[Distance]

@strawberry.type
class MetricDistances:
    project_id: str
    distances: List[Distances]

@strawberry.type
class Histogram:
    last_updated: int
    metrics: List[Metric]

@strawberry.type
class OverallStats:
    project_id: str
    histograms: List[Histogram]

@strawberry.type
class DataEntry:
    timestamp: str
    url: str

@strawberry.type
class MetricData:
    metric: str
    submetric: Optional[str]
    data: List[DataEntry]

@strawberry.type
class MetricType:
    metrictype: str
    data: List[MetricData]

@strawberry.type
class SensorType:
    sensorId: str
    timestamp: str
    data: List[MetricType]

@strawberry.type
class Project:
    projectName: str
    status: str
    data: List[SensorType]
