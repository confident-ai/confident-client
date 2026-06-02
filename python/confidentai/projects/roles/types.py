from typing import List, Optional

from pydantic import Field

from ...types import ConfidentBaseModel, Role


class RoleRequest(ConfidentBaseModel):
    name: str
    policy_ids: List[str] = Field(alias="policyIds")
    description: Optional[str] = None


class RoleHttpResponse(ConfidentBaseModel):
    role: Role


class RolesHttpResponse(ConfidentBaseModel):
    roles: List[Role] = Field(default_factory=list)
