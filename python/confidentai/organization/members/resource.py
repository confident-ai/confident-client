from typing import List, Optional

from ...api import Api, Endpoints, HttpMethods
from ...types import DeletionResult, Member
from .types import (
    MemberHttpResponse,
    MembersHttpResponse,
    UpdateMemberRoleRequest,
)


class OrganizationMembers:
    def __init__(self, api: Api) -> None:
        self._api = api

    def list(
        self,
        *,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> List[Member]:
        data, _ = self._api.send_request(
            HttpMethods.GET,
            Endpoints.ORGANIZATION_MEMBERS_ENDPOINT,
            params={"page": page, "pageSize": page_size},
        )
        return MembersHttpResponse(**data).members

    def update_role(self, user_id: str, *, role_id: str) -> Member:
        body = UpdateMemberRoleRequest(role_id=role_id).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = self._api.send_request(
            HttpMethods.PUT,
            Endpoints.ORGANIZATION_MEMBER_ENDPOINT,
            body=body,
            url_params={"userId": user_id},
        )
        return MemberHttpResponse(**data).member

    def remove(self, user_id: str) -> DeletionResult:
        data, _ = self._api.send_request(
            HttpMethods.DELETE,
            Endpoints.ORGANIZATION_MEMBER_ENDPOINT,
            url_params={"userId": user_id},
        )
        return DeletionResult(**data)


class AsyncOrganizationMembers:
    def __init__(self, api: Api) -> None:
        self._api = api

    async def list(
        self,
        *,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> List[Member]:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET,
            Endpoints.ORGANIZATION_MEMBERS_ENDPOINT,
            params={"page": page, "pageSize": page_size},
        )
        return MembersHttpResponse(**data).members

    async def update_role(self, user_id: str, *, role_id: str) -> Member:
        body = UpdateMemberRoleRequest(role_id=role_id).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = await self._api.a_send_request(
            HttpMethods.PUT,
            Endpoints.ORGANIZATION_MEMBER_ENDPOINT,
            body=body,
            url_params={"userId": user_id},
        )
        return MemberHttpResponse(**data).member

    async def remove(self, user_id: str) -> DeletionResult:
        data, _ = await self._api.a_send_request(
            HttpMethods.DELETE,
            Endpoints.ORGANIZATION_MEMBER_ENDPOINT,
            url_params={"userId": user_id},
        )
        return DeletionResult(**data)
