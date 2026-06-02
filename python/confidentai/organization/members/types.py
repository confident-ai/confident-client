from typing import List

from pydantic import Field

from ...types import ConfidentBaseModel, Member


class UpdateMemberRoleRequest(ConfidentBaseModel):
    role_id: str = Field(alias="roleId")


class MemberHttpResponse(ConfidentBaseModel):
    member: Member


class MembersHttpResponse(ConfidentBaseModel):
    members: List[Member] = Field(default_factory=list)
