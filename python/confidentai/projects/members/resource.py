from typing import List, Optional

from ...api import Api, Endpoints, HttpMethods
from ...types import DeletionResult, Member
from .types import (
    MemberHttpResponse,
    MembersHttpResponse,
    UpdateMemberRoleRequest,
)


class ProjectMembers:
    def __init__(self, api: Api, project_id: str) -> None:
        self._api = api
        self._project_id = project_id

    def list(
        self,
        *,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> List[Member]:
        data, _ = self._api.send_request(
            HttpMethods.GET,
            Endpoints.PROJECT_MEMBERS_ENDPOINT,
            params={"page": page, "pageSize": page_size},
            url_params={"projectId": self._project_id},
        )
        return MembersHttpResponse(**data).members

    def update_role(self, user_id: str, *, role_id: str) -> Member:
        body = UpdateMemberRoleRequest(role_id=role_id).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = self._api.send_request(
            HttpMethods.PUT,
            Endpoints.PROJECT_MEMBER_ENDPOINT,
            body=body,
            url_params={"projectId": self._project_id, "userId": user_id},
        )
        return MemberHttpResponse(**data).member

    def remove(self, user_id: str) -> DeletionResult:
        data, _ = self._api.send_request(
            HttpMethods.DELETE,
            Endpoints.PROJECT_MEMBER_ENDPOINT,
            url_params={"projectId": self._project_id, "userId": user_id},
        )
        return DeletionResult(**data)


class AsyncProjectMembers:
    def __init__(self, api: Api, project_id: str) -> None:
        self._api = api
        self._project_id = project_id

    async def list(
        self,
        *,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> List[Member]:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET,
            Endpoints.PROJECT_MEMBERS_ENDPOINT,
            params={"page": page, "pageSize": page_size},
            url_params={"projectId": self._project_id},
        )
        return MembersHttpResponse(**data).members

    async def update_role(self, user_id: str, *, role_id: str) -> Member:
        body = UpdateMemberRoleRequest(role_id=role_id).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = await self._api.a_send_request(
            HttpMethods.PUT,
            Endpoints.PROJECT_MEMBER_ENDPOINT,
            body=body,
            url_params={"projectId": self._project_id, "userId": user_id},
        )
        return MemberHttpResponse(**data).member

    async def remove(self, user_id: str) -> DeletionResult:
        data, _ = await self._api.a_send_request(
            HttpMethods.DELETE,
            Endpoints.PROJECT_MEMBER_ENDPOINT,
            url_params={"projectId": self._project_id, "userId": user_id},
        )
        return DeletionResult(**data)
