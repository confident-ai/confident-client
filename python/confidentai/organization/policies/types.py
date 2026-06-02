from typing import List, Optional

from pydantic import Field

from ...types import ConfidentBaseModel, Policy


class PolicyRequest(ConfidentBaseModel):
    name: str
    permission_ids: List[str] = Field(alias="permissionIds")
    description: Optional[str] = None


class PolicyHttpResponse(ConfidentBaseModel):
    policy: Policy


class PoliciesHttpResponse(ConfidentBaseModel):
    policies: List[Policy] = Field(default_factory=list)
