import models
import strawberry

@strawberry.type
class Query:
    @strawberry.field
    def projects(self) -> List[Project]:
        projects = []
        for project_data in collection.find():
            project = Project(id=project_data["id"], name=project_name["name"])
            projects.append(project)
        return projects

    @strawberry.field
    def project(self, id: int) -> Project:
        project_data = collection.find_one({"id": id})
        if project_data:
            return Project(id=project_data["id"], name=project_data["name"])
        else:
            return None

    @strawberry.field
    def overall_stats(self, id: int) -> OverallStats:
        stats_data = collection.find_one({"projectid": id})
        if stats_data:
            return stats_data
        else:
            return None


