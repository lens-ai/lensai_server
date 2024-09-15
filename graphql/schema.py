import strawberry
from typing import Optional, List
from models import Metric, Project, MetricDistances
from resolvers import get_metric_stats, fetch_project_data, get_metric_distances

@strawberry.type
class Query:
    @strawberry.field
    def metric_stats(self, project_id: str, metric: str, submetric: Optional[str] = None, reference: Optional[bool] = False) -> Optional[Metric]:
        return get_metric_stats(project_id, metric, submetric, reference)

    @strawberry.field 
    def project(self, projectName: str, metrictype: Optional[str] = None, metric: Optional[str] = None, submetric: Optional[str] = None, timestamp: Optional[str] = None, sensorId: Optional[str] = None) -> Project:
        return fetch_project_data(projectName, metrictype, metric, submetric, timestamp, sensorId)

    @strawberry.field
    def metric_distances(self, project_id: str) -> Optional[MetricDistances]:
        return get_metric_distances(project_id)

schema = strawberry.Schema(query=Query)
