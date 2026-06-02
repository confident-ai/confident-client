from typing import List, Optional

from ...api import Api, Endpoints, HttpMethods
from ...types import DeletionResult, Invitation
from .types import (
    CreateOrganizationInvitationsRequest,
    InvitationHttpResponse,
    InvitationsHttpResponse,
)


class OrganizationInvitations:
    def __init__(self, api: Api) -> None:
        self._api = api

    def list(self) -> List[Invitation]:
        data, _ = self._api.send_request(
            HttpMethods.GET, Endpoints.ORGANIZATION_INVITATIONS_ENDPOINT
        )
        return InvitationsHttpResponse(**data).invitations

    def create(
        self,
        emails: List[str],
        *,
        role_id: Optional[str] = None,
    ) -> List[Invitation]:
        body = CreateOrganizationInvitationsRequest(
            emails=emails, role_id=role_id
        ).model_dump(by_alias=True, exclude_none=True)
        data, _ = self._api.send_request(
            HttpMethods.POST,
            Endpoints.ORGANIZATION_INVITATIONS_ENDPOINT,
            body=body,
        )
        return InvitationsHttpResponse(**data).invitations

    def resend(self, invitation_id: int) -> Invitation:
        data, _ = self._api.send_request(
            HttpMethods.PUT,
            Endpoints.ORGANIZATION_INVITATION_ENDPOINT,
            url_params={"invitationId": invitation_id},
        )
        return InvitationHttpResponse(**data).invitation

    def revoke(self, invitation_id: int) -> DeletionResult:
        data, _ = self._api.send_request(
            HttpMethods.DELETE,
            Endpoints.ORGANIZATION_INVITATION_ENDPOINT,
            url_params={"invitationId": invitation_id},
        )
        return DeletionResult(**data)


class AsyncOrganizationInvitations:
    def __init__(self, api: Api) -> None:
        self._api = api

    async def list(self) -> List[Invitation]:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET, Endpoints.ORGANIZATION_INVITATIONS_ENDPOINT
        )
        return InvitationsHttpResponse(**data).invitations

    async def create(
        self,
        emails: List[str],
        *,
        role_id: Optional[str] = None,
    ) -> List[Invitation]:
        body = CreateOrganizationInvitationsRequest(
            emails=emails, role_id=role_id
        ).model_dump(by_alias=True, exclude_none=True)
        data, _ = await self._api.a_send_request(
            HttpMethods.POST,
            Endpoints.ORGANIZATION_INVITATIONS_ENDPOINT,
            body=body,
        )
        return InvitationsHttpResponse(**data).invitations

    async def resend(self, invitation_id: int) -> Invitation:
        data, _ = await self._api.a_send_request(
            HttpMethods.PUT,
            Endpoints.ORGANIZATION_INVITATION_ENDPOINT,
            url_params={"invitationId": invitation_id},
        )
        return InvitationHttpResponse(**data).invitation

    async def revoke(self, invitation_id: int) -> DeletionResult:
        data, _ = await self._api.a_send_request(
            HttpMethods.DELETE,
            Endpoints.ORGANIZATION_INVITATION_ENDPOINT,
            url_params={"invitationId": invitation_id},
        )
        return DeletionResult(**data)
