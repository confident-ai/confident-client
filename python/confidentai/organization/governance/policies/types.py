from typing import List

from pydantic import Field

from ....types import ConfidentBaseModel, GovernancePolicy


class AssignProjectsRequest(ConfidentBaseModel):
    project_ids: List[str] = Field(alias="projectIds")


class GovernancePoliciesHttpResponse(ConfidentBaseModel):
    governance_policies: List[GovernancePolicy] = Field(
        default_factory=list, alias="governancePolicies"
    )
