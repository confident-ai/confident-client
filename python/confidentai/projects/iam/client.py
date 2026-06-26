from ...api import Api
from .permissions import AsyncProjectPermissions, ProjectPermissions
from .policies import AsyncProjectPolicies, ProjectPolicies
from .roles import AsyncProjectRoles, ProjectRoles


class ProjectIam:
    def __init__(self, api: Api, project_id: str) -> None:
        self.policies = ProjectPolicies(api, project_id)
        self.roles = ProjectRoles(api, project_id)
        self.permissions = ProjectPermissions(api, project_id)


class AsyncProjectIam:
    def __init__(self, api: Api, project_id: str) -> None:
        self.policies = AsyncProjectPolicies(api, project_id)
        self.roles = AsyncProjectRoles(api, project_id)
        self.permissions = AsyncProjectPermissions(api, project_id)
