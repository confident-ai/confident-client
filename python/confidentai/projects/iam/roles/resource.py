from typing import List, Optional

from ....api import Api, Endpoints, HttpMethods
from ....types import DeletionResult, Role
from .types import RoleHttpResponse, RoleRequest, RolesHttpResponse


class ProjectRoles:
    def __init__(self, api: Api, project_id: str) -> None:
        self._api = api
        self._project_id = project_id

    def list(self) -> List[Role]:
        data, _ = self._api.send_request(
            HttpMethods.GET,
            Endpoints.PROJECT_ROLES_ENDPOINT,
            url_params={"projectId": self._project_id},
        )
        return RolesHttpResponse(**data).roles

    def create(
        self,
        name: str,
        *,
        policy_ids: List[str],
        description: Optional[str] = None,
    ) -> Role:
        body = RoleRequest(
            name=name, policy_ids=policy_ids, description=description
        ).model_dump(by_alias=True, exclude_none=True)
        data, _ = self._api.send_request(
            HttpMethods.POST,
            Endpoints.PROJECT_ROLES_ENDPOINT,
            body=body,
            url_params={"projectId": self._project_id},
        )
        return RoleHttpResponse(**data).role

    def update(
        self,
        role_id: str,
        *,
        name: str,
        policy_ids: List[str],
        description: Optional[str] = None,
    ) -> Role:
        body = RoleRequest(
            name=name, policy_ids=policy_ids, description=description
        ).model_dump(by_alias=True, exclude_none=True)
        data, _ = self._api.send_request(
            HttpMethods.PUT,
            Endpoints.PROJECT_ROLE_ENDPOINT,
            body=body,
            url_params={"projectId": self._project_id, "roleId": role_id},
        )
        return RoleHttpResponse(**data).role

    def delete(self, role_id: str) -> DeletionResult:
        data, _ = self._api.send_request(
            HttpMethods.DELETE,
            Endpoints.PROJECT_ROLE_ENDPOINT,
            url_params={"projectId": self._project_id, "roleId": role_id},
        )
        return DeletionResult(**data)


class AsyncProjectRoles:
    def __init__(self, api: Api, project_id: str) -> None:
        self._api = api
        self._project_id = project_id

    async def list(self) -> List[Role]:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET,
            Endpoints.PROJECT_ROLES_ENDPOINT,
            url_params={"projectId": self._project_id},
        )
        return RolesHttpResponse(**data).roles

    async def create(
        self,
        name: str,
        *,
        policy_ids: List[str],
        description: Optional[str] = None,
    ) -> Role:
        body = RoleRequest(
            name=name, policy_ids=policy_ids, description=description
        ).model_dump(by_alias=True, exclude_none=True)
        data, _ = await self._api.a_send_request(
            HttpMethods.POST,
            Endpoints.PROJECT_ROLES_ENDPOINT,
            body=body,
            url_params={"projectId": self._project_id},
        )
        return RoleHttpResponse(**data).role

    async def update(
        self,
        role_id: str,
        *,
        name: str,
        policy_ids: List[str],
        description: Optional[str] = None,
    ) -> Role:
        body = RoleRequest(
            name=name, policy_ids=policy_ids, description=description
        ).model_dump(by_alias=True, exclude_none=True)
        data, _ = await self._api.a_send_request(
            HttpMethods.PUT,
            Endpoints.PROJECT_ROLE_ENDPOINT,
            body=body,
            url_params={"projectId": self._project_id, "roleId": role_id},
        )
        return RoleHttpResponse(**data).role

    async def delete(self, role_id: str) -> DeletionResult:
        data, _ = await self._api.a_send_request(
            HttpMethods.DELETE,
            Endpoints.PROJECT_ROLE_ENDPOINT,
            url_params={"projectId": self._project_id, "roleId": role_id},
        )
        return DeletionResult(**data)
