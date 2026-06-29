from typing import List, Optional

from ....api import Api, Endpoints, HttpMethods
from ....types import DeletionResult, Role
from .types import RoleHttpResponse, RoleRequest, RolesHttpResponse


class OrganizationRoles:
    def __init__(self, api: Api) -> None:
        self._api = api

    def list(self) -> List[Role]:
        data, _ = self._api.send_request(
            HttpMethods.GET, Endpoints.ORGANIZATION_ROLES_ENDPOINT
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
            Endpoints.ORGANIZATION_ROLES_ENDPOINT,
            body=body,
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
            Endpoints.ORGANIZATION_ROLE_ENDPOINT,
            body=body,
            url_params={"roleId": role_id},
        )
        return RoleHttpResponse(**data).role

    def delete(self, role_id: str) -> DeletionResult:
        data, _ = self._api.send_request(
            HttpMethods.DELETE,
            Endpoints.ORGANIZATION_ROLE_ENDPOINT,
            url_params={"roleId": role_id},
        )
        return DeletionResult(**data)

    async def a_list(self) -> List[Role]:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET, Endpoints.ORGANIZATION_ROLES_ENDPOINT
        )
        return RolesHttpResponse(**data).roles

    async def a_create(
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
            Endpoints.ORGANIZATION_ROLES_ENDPOINT,
            body=body,
        )
        return RoleHttpResponse(**data).role

    async def a_update(
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
            Endpoints.ORGANIZATION_ROLE_ENDPOINT,
            body=body,
            url_params={"roleId": role_id},
        )
        return RoleHttpResponse(**data).role

    async def a_delete(self, role_id: str) -> DeletionResult:
        data, _ = await self._api.a_send_request(
            HttpMethods.DELETE,
            Endpoints.ORGANIZATION_ROLE_ENDPOINT,
            url_params={"roleId": role_id},
        )
        return DeletionResult(**data)
