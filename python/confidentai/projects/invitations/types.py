from typing import List, Optional

from pydantic import Field

from ...types import ConfidentBaseModel, Invitation


class CreateProjectInvitationsRequest(ConfidentBaseModel):
    emails: List[str]
    role_id: Optional[str] = Field(default=None, alias="projectRoleId")


class InvitationHttpResponse(ConfidentBaseModel):
    invitation: Invitation


class InvitationsHttpResponse(ConfidentBaseModel):
    invitations: List[Invitation] = Field(default_factory=list)
