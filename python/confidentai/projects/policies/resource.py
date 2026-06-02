from typing import List, Optional

from ...api import Api, Endpoints, HttpMethods
from ...types import DeletionResult, Policy
from .types import PoliciesHttpResponse, PolicyHttpResponse, PolicyRequest


class ProjectPolicies:
    def __init__(self, api: Api, project_id: str) -> None:
        self._api = api
        self._project_id = project_id

    def list(self) -> List[Policy]:
        data, _ = self._api.send_request(
            HttpMethods.GET,
            Endpoints.PROJECT_POLICIES_ENDPOINT,
            url_params={"projectId": self._project_id},
        )
        return PoliciesHttpResponse(**data).policies

    def create(
        self,
        name: str,
        *,
        permission_ids: List[str],
        description: Optional[str] = None,
    ) -> Policy:
        body = PolicyRequest(
            name=name, permission_ids=permission_ids, description=description
        ).model_dump(by_alias=True, exclude_none=True)
        data, _ = self._api.send_request(
            HttpMethods.POST,
            Endpoints.PROJECT_POLICIES_ENDPOINT,
            body=body,
            url_params={"projectId": self._project_id},
        )
        return PolicyHttpResponse(**data).policy

    def update(
        self,
        policy_id: str,
        *,
        name: str,
        permission_ids: List[str],
        description: Optional[str] = None,
    ) -> Policy:
        body = PolicyRequest(
            name=name, permission_ids=permission_ids, description=description
        ).model_dump(by_alias=True, exclude_none=True)
        data, _ = self._api.send_request(
            HttpMethods.PUT,
            Endpoints.PROJECT_POLICY_ENDPOINT,
            body=body,
            url_params={"projectId": self._project_id, "policyId": policy_id},
        )
        return PolicyHttpResponse(**data).policy

    def delete(self, policy_id: str) -> DeletionResult:
        data, _ = self._api.send_request(
            HttpMethods.DELETE,
            Endpoints.PROJECT_POLICY_ENDPOINT,
            url_params={"projectId": self._project_id, "policyId": policy_id},
        )
        return DeletionResult(**data)


class AsyncProjectPolicies:
    def __init__(self, api: Api, project_id: str) -> None:
        self._api = api
        self._project_id = project_id

    async def list(self) -> List[Policy]:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET,
            Endpoints.PROJECT_POLICIES_ENDPOINT,
            url_params={"projectId": self._project_id},
        )
        return PoliciesHttpResponse(**data).policies

    async def create(
        self,
        name: str,
        *,
        permission_ids: List[str],
        description: Optional[str] = None,
    ) -> Policy:
        body = PolicyRequest(
            name=name, permission_ids=permission_ids, description=description
        ).model_dump(by_alias=True, exclude_none=True)
        data, _ = await self._api.a_send_request(
            HttpMethods.POST,
            Endpoints.PROJECT_POLICIES_ENDPOINT,
            body=body,
            url_params={"projectId": self._project_id},
        )
        return PolicyHttpResponse(**data).policy

    async def update(
        self,
        policy_id: str,
        *,
        name: str,
        permission_ids: List[str],
        description: Optional[str] = None,
    ) -> Policy:
        body = PolicyRequest(
            name=name, permission_ids=permission_ids, description=description
        ).model_dump(by_alias=True, exclude_none=True)
        data, _ = await self._api.a_send_request(
            HttpMethods.PUT,
            Endpoints.PROJECT_POLICY_ENDPOINT,
            body=body,
            url_params={"projectId": self._project_id, "policyId": policy_id},
        )
        return PolicyHttpResponse(**data).policy

    async def delete(self, policy_id: str) -> DeletionResult:
        data, _ = await self._api.a_send_request(
            HttpMethods.DELETE,
            Endpoints.PROJECT_POLICY_ENDPOINT,
            url_params={"projectId": self._project_id, "policyId": policy_id},
        )
        return DeletionResult(**data)
