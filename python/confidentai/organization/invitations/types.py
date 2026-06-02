from typing import List, Optional

from pydantic import Field

from ...types import ConfidentBaseModel, Invitation


class CreateOrganizationInvitationsRequest(ConfidentBaseModel):
    emails: List[str]
    role_id: Optional[str] = Field(default=None, alias="organizationRoleId")


class InvitationHttpResponse(ConfidentBaseModel):
    invitation: Invitation


class InvitationsHttpResponse(ConfidentBaseModel):
    invitations: List[Invitation] = Field(default_factory=list)
