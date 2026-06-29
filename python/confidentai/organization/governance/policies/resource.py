from typing import List, Optional

from ....api import Api, Endpoints, HttpMethods
from ....types import (
    GovernancePolicy,
    GovernancePolicyAssignmentResult,
    GovernancePolicyUnassignmentResult,
    NamedRef,
)
from .types import (
    GovernancePoliciesHttpResponse,
    GovernancePolicyProjectsHttpResponse,
    ProjectIdsRequest,
)


class OrganizationGovernancePolicies:
    def __init__(self, api: Api) -> None:
        self._api = api

    def list(self) -> List[GovernancePolicy]:
        data, _ = self._api.send_request(
            HttpMethods.GET,
            Endpoints.ORGANIZATION_GOVERNANCE_POLICIES_ENDPOINT,
        )
        return GovernancePoliciesHttpResponse(**data).governance_policies

    def list_projects(
        self,
        policy_id: str,
        *,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> List[NamedRef]:
        data, _ = self._api.send_request(
            HttpMethods.GET,
            Endpoints.ORGANIZATION_GOVERNANCE_POLICY_PROJECTS_ENDPOINT,
            params={"page": page, "pageSize": page_size},
            url_params={"policyId": policy_id},
        )
        return GovernancePolicyProjectsHttpResponse(**data).projects

    def assign(
        self, policy_id: str, *, project_ids: List[str]
    ) -> GovernancePolicyAssignmentResult:
        body = ProjectIdsRequest(project_ids=project_ids).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = self._api.send_request(
            HttpMethods.POST,
            Endpoints.ORGANIZATION_GOVERNANCE_POLICY_ASSIGN_ENDPOINT,
            body=body,
            url_params={"policyId": policy_id},
        )
        return GovernancePolicyAssignmentResult(**data)

    def unassign(
        self, policy_id: str, *, project_ids: List[str]
    ) -> GovernancePolicyUnassignmentResult:
        body = ProjectIdsRequest(project_ids=project_ids).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = self._api.send_request(
            HttpMethods.POST,
            Endpoints.ORGANIZATION_GOVERNANCE_POLICY_UNASSIGN_ENDPOINT,
            body=body,
            url_params={"policyId": policy_id},
        )
        return GovernancePolicyUnassignmentResult(**data)

    async def a_list(self) -> List[GovernancePolicy]:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET,
            Endpoints.ORGANIZATION_GOVERNANCE_POLICIES_ENDPOINT,
        )
        return GovernancePoliciesHttpResponse(**data).governance_policies

    async def a_list_projects(
        self,
        policy_id: str,
        *,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> List[NamedRef]:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET,
            Endpoints.ORGANIZATION_GOVERNANCE_POLICY_PROJECTS_ENDPOINT,
            params={"page": page, "pageSize": page_size},
            url_params={"policyId": policy_id},
        )
        return GovernancePolicyProjectsHttpResponse(**data).projects

    async def a_assign(
        self, policy_id: str, *, project_ids: List[str]
    ) -> GovernancePolicyAssignmentResult:
        body = ProjectIdsRequest(project_ids=project_ids).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = await self._api.a_send_request(
            HttpMethods.POST,
            Endpoints.ORGANIZATION_GOVERNANCE_POLICY_ASSIGN_ENDPOINT,
            body=body,
            url_params={"policyId": policy_id},
        )
        return GovernancePolicyAssignmentResult(**data)

    async def a_unassign(
        self, policy_id: str, *, project_ids: List[str]
    ) -> GovernancePolicyUnassignmentResult:
        body = ProjectIdsRequest(project_ids=project_ids).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = await self._api.a_send_request(
            HttpMethods.POST,
            Endpoints.ORGANIZATION_GOVERNANCE_POLICY_UNASSIGN_ENDPOINT,
            body=body,
            url_params={"policyId": policy_id},
        )
        return GovernancePolicyUnassignmentResult(**data)
