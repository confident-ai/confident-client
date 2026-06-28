from ...api import Api
from .permissions import ProjectPermissions
from .policies import ProjectPolicies
from .roles import ProjectRoles


class ProjectIam:
    def __init__(self, api: Api, project_id: str) -> None:
        self.policies = ProjectPolicies(api, project_id)
        self.roles = ProjectRoles(api, project_id)
        self.permissions = ProjectPermissions(api, project_id)
