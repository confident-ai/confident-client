from typing import List, Optional

from ...api import Api, Endpoints, HttpMethods
from ...types import DeletionResult, Invitation
from .types import (
    CreateProjectInvitationsRequest,
    InvitationHttpResponse,
    InvitationsHttpResponse,
)


class ProjectInvitations:
    def __init__(self, api: Api, project_id: str) -> None:
        self._api = api
        self._project_id = project_id

    def list(self) -> List[Invitation]:
        data, _ = self._api.send_request(
            HttpMethods.GET,
            Endpoints.PROJECT_INVITATIONS_ENDPOINT,
            url_params={"projectId": self._project_id},
        )
        return InvitationsHttpResponse(**data).invitations

    def create(
        self,
        emails: List[str],
        *,
        role_id: Optional[str] = None,
    ) -> List[Invitation]:
        body = CreateProjectInvitationsRequest(
            emails=emails, role_id=role_id
        ).model_dump(by_alias=True, exclude_none=True)
        data, _ = self._api.send_request(
            HttpMethods.POST,
            Endpoints.PROJECT_INVITATIONS_ENDPOINT,
            body=body,
            url_params={"projectId": self._project_id},
        )
        return InvitationsHttpResponse(**data).invitations

    def resend(self, invitation_id: int) -> Invitation:
        data, _ = self._api.send_request(
            HttpMethods.PUT,
            Endpoints.PROJECT_INVITATION_ENDPOINT,
            url_params={
                "projectId": self._project_id,
                "invitationId": invitation_id,
            },
        )
        return InvitationHttpResponse(**data).invitation

    def revoke(self, invitation_id: int) -> DeletionResult:
        data, _ = self._api.send_request(
            HttpMethods.DELETE,
            Endpoints.PROJECT_INVITATION_ENDPOINT,
            url_params={
                "projectId": self._project_id,
                "invitationId": invitation_id,
            },
        )
        return DeletionResult(**data)


class AsyncProjectInvitations:
    def __init__(self, api: Api, project_id: str) -> None:
        self._api = api
        self._project_id = project_id

    async def list(self) -> List[Invitation]:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET,
            Endpoints.PROJECT_INVITATIONS_ENDPOINT,
            url_params={"projectId": self._project_id},
        )
        return InvitationsHttpResponse(**data).invitations

    async def create(
        self,
        emails: List[str],
        *,
        role_id: Optional[str] = None,
    ) -> List[Invitation]:
        body = CreateProjectInvitationsRequest(
            emails=emails, role_id=role_id
        ).model_dump(by_alias=True, exclude_none=True)
        data, _ = await self._api.a_send_request(
            HttpMethods.POST,
            Endpoints.PROJECT_INVITATIONS_ENDPOINT,
            body=body,
            url_params={"projectId": self._project_id},
        )
        return InvitationsHttpResponse(**data).invitations

    async def resend(self, invitation_id: int) -> Invitation:
        data, _ = await self._api.a_send_request(
            HttpMethods.PUT,
            Endpoints.PROJECT_INVITATION_ENDPOINT,
            url_params={
                "projectId": self._project_id,
                "invitationId": invitation_id,
            },
        )
        return InvitationHttpResponse(**data).invitation

    async def revoke(self, invitation_id: int) -> DeletionResult:
        data, _ = await self._api.a_send_request(
            HttpMethods.DELETE,
            Endpoints.PROJECT_INVITATION_ENDPOINT,
            url_params={
                "projectId": self._project_id,
                "invitationId": invitation_id,
            },
        )
        return DeletionResult(**data)
