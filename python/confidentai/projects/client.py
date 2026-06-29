from typing import List, Optional

from ..api import Api, Endpoints, HttpMethods
from ..types import CreatedProject, DeletionResult, Project
from ..utils.validation import require
from .api_keys import ProjectApiKeys
from .iam import ProjectIam
from .invitations import ProjectInvitations
from .members import ProjectMembers
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

    async def a_list(self) -> List[Project]:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET, Endpoints.PROJECTS_ENDPOINT
        )
        return ProjectsHttpResponse(**data).projects

    async def a_create(
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


class ProjectClient:
    def __init__(self, api: Api, project_id: str) -> None:
        require(project_id, "project_id is required")
        self._api = api
        self.project_id = project_id

        self.api_keys = ProjectApiKeys(api, project_id)
        self.members = ProjectMembers(api, project_id)
        self.invitations = ProjectInvitations(api, project_id)
        self.iam = ProjectIam(api, project_id)

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

    async def a_get(self) -> Project:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET,
            Endpoints.PROJECT_ENDPOINT,
            url_params={"projectId": self.project_id},
        )
        return ProjectHttpResponse(**data).project

    async def a_update(
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

    async def a_delete(self) -> DeletionResult:
        data, _ = await self._api.a_send_request(
            HttpMethods.DELETE,
            Endpoints.PROJECT_ENDPOINT,
            url_params={"projectId": self.project_id},
        )
        return DeletionResult(**data)
