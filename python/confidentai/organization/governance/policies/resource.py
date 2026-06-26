from typing import List

from ....api import Api, Endpoints, HttpMethods
from ....types import GovernancePolicy, GovernancePolicyAssignmentResult
from .types import AssignProjectsRequest, GovernancePoliciesHttpResponse


class GovernancePolicies:
    def __init__(self, api: Api) -> None:
        self._api = api

    def list(self) -> List[GovernancePolicy]:
        data, _ = self._api.send_request(
            HttpMethods.GET,
            Endpoints.ORGANIZATION_GOVERNANCE_POLICIES_ENDPOINT,
        )
        return GovernancePoliciesHttpResponse(**data).governance_policies

    def assign(
        self, policy_id: str, *, project_ids: List[str]
    ) -> GovernancePolicyAssignmentResult:
        body = AssignProjectsRequest(project_ids=project_ids).model_dump(
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
    ) -> GovernancePolicyAssignmentResult:
        body = AssignProjectsRequest(project_ids=project_ids).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = self._api.send_request(
            HttpMethods.POST,
            Endpoints.ORGANIZATION_GOVERNANCE_POLICY_UNASSIGN_ENDPOINT,
            body=body,
            url_params={"policyId": policy_id},
        )
        return GovernancePolicyAssignmentResult(**data)


class AsyncGovernancePolicies:
    def __init__(self, api: Api) -> None:
        self._api = api

    async def list(self) -> List[GovernancePolicy]:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET,
            Endpoints.ORGANIZATION_GOVERNANCE_POLICIES_ENDPOINT,
        )
        return GovernancePoliciesHttpResponse(**data).governance_policies

    async def assign(
        self, policy_id: str, *, project_ids: List[str]
    ) -> GovernancePolicyAssignmentResult:
        body = AssignProjectsRequest(project_ids=project_ids).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = await self._api.a_send_request(
            HttpMethods.POST,
            Endpoints.ORGANIZATION_GOVERNANCE_POLICY_ASSIGN_ENDPOINT,
            body=body,
            url_params={"policyId": policy_id},
        )
        return GovernancePolicyAssignmentResult(**data)

    async def unassign(
        self, policy_id: str, *, project_ids: List[str]
    ) -> GovernancePolicyAssignmentResult:
        body = AssignProjectsRequest(project_ids=project_ids).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = await self._api.a_send_request(
            HttpMethods.POST,
            Endpoints.ORGANIZATION_GOVERNANCE_POLICY_UNASSIGN_ENDPOINT,
            body=body,
            url_params={"policyId": policy_id},
        )
        return GovernancePolicyAssignmentResult(**data)
