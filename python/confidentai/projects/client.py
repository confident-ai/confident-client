from typing import List, Optional

from ..api import Api, Endpoints, HttpMethods
from ..types import CreatedProject, DeletionResult, Project
from ..utils.validation import require
from .api_keys import AsyncProjectApiKeys, ProjectApiKeys
from .invitations import AsyncProjectInvitations, ProjectInvitations
from .members import AsyncProjectMembers, ProjectMembers
from .permissions import AsyncProjectPermissions, ProjectPermissions
from .policies import AsyncProjectPolicies, ProjectPolicies
from .roles import AsyncProjectRoles, ProjectRoles
from .types import (
    CreateProjectRequest,
    ProjectHttpResponse,
    ProjectsHttpResponse,
    UpdateProjectRequest,
)


class ProjectsClient:
    def __init__(self, api: Api) -> None:
        self._api = api

    def list(self) -> List[Project]:
        data, _ = self._api.send_request(
            HttpMethods.GET, Endpoints.PROJECTS_ENDPOINT
        )
        return ProjectsHttpResponse(**data).projects

    def create(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        email: Optional[str] = None,
    ) -> CreatedProject:
        body = CreateProjectRequest(
            name=name, description=description, email=email
        ).model_dump(by_alias=True, exclude_none=True)
        data, _ = self._api.send_request(
            HttpMethods.POST,
            Endpoints.PROJECTS_ENDPOINT,
            body=body,
        )
        return CreatedProject(**data)


class ProjectClient:
    def __init__(self, api: Api, project_id: str) -> None:
        require(project_id, "project_id is required")
        self._api = api
        self.project_id = project_id

        self.api_keys = ProjectApiKeys(api, project_id)
        self.members = ProjectMembers(api, project_id)
        self.invitations = ProjectInvitations(api, project_id)
        self.roles = ProjectRoles(api, project_id)
        self.policies = ProjectPolicies(api, project_id)
        self.permissions = ProjectPermissions(api, project_id)

    def get(self) -> Project:
        data, _ = self._api.send_request(
            HttpMethods.GET,
            Endpoints.PROJECT_ENDPOINT,
            url_params={"projectId": self.project_id},
        )
        return ProjectHttpResponse(**data).project

    def update(
        self,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Project:
        body = UpdateProjectRequest(
            name=name, description=description
        ).model_dump(by_alias=True, exclude_none=True)
        data, _ = self._api.send_request(
            HttpMethods.PUT,
            Endpoints.PROJECT_ENDPOINT,
            body=body,
            url_params={"projectId": self.project_id},
        )
        return ProjectHttpResponse(**data).project

    def delete(self) -> DeletionResult:
        data, _ = self._api.send_request(
            HttpMethods.DELETE,
            Endpoints.PROJECT_ENDPOINT,
            url_params={"projectId": self.project_id},
        )
        return DeletionResult(**data)


class AsyncProjectsClient:
    def __init__(self, api: Api) -> None:
        self._api = api

    async def list(self) -> List[Project]:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET, Endpoints.PROJECTS_ENDPOINT
        )
        return ProjectsHttpResponse(**data).projects

    async def create(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        email: Optional[str] = None,
    ) -> CreatedProject:
        body = CreateProjectRequest(
            name=name, description=description, email=email
        ).model_dump(by_alias=True, exclude_none=True)
        data, _ = await self._api.a_send_request(
            HttpMethods.POST,
            Endpoints.PROJECTS_ENDPOINT,
            body=body,
        )
        return CreatedProject(**data)


class AsyncProjectClient:
    def __init__(self, api: Api, project_id: str) -> None:
        require(project_id, "project_id is required")
        self._api = api
        self.project_id = project_id

        self.api_keys = AsyncProjectApiKeys(api, project_id)
        self.members = AsyncProjectMembers(api, project_id)
        self.invitations = AsyncProjectInvitations(api, project_id)
        self.roles = AsyncProjectRoles(api, project_id)
        self.policies = AsyncProjectPolicies(api, project_id)
        self.permissions = AsyncProjectPermissions(api, project_id)

    async def get(self) -> Project:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET,
            Endpoints.PROJECT_ENDPOINT,
            url_params={"projectId": self.project_id},
        )
        return ProjectHttpResponse(**data).project

    async def update(
        self,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Project:
        body = UpdateProjectRequest(
            name=name, description=description
        ).model_dump(by_alias=True, exclude_none=True)
        data, _ = await self._api.a_send_request(
            HttpMethods.PUT,
            Endpoints.PROJECT_ENDPOINT,
            body=body,
            url_params={"projectId": self.project_id},
        )
        return ProjectHttpResponse(**data).project

    async def delete(self) -> DeletionResult:
        data, _ = await self._api.a_send_request(
            HttpMethods.DELETE,
            Endpoints.PROJECT_ENDPOINT,
            url_params={"projectId": self.project_id},
        )
        return DeletionResult(**data)
