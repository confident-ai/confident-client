from ..api import Api, Endpoints, HttpMethods
from ..types import Organization
from .api_keys import OrganizationApiKeys
from .governance import OrganizationGovernance
from .iam import OrganizationIam
from .invitations import OrganizationInvitations
from .members import OrganizationMembers
from .types import OrganizationHttpResponse, UpdateOrganizationRequest


class OrganizationClient:
    def __init__(self, api: Api) -> None:
        self._api = api
        self.api_keys = OrganizationApiKeys(api)
        self.members = OrganizationMembers(api)
        self.invitations = OrganizationInvitations(api)
        self.iam = OrganizationIam(api)
        self.governance = OrganizationGovernance(api)

    def get(self) -> Organization:
        data, _ = self._api.send_request(
            HttpMethods.GET, Endpoints.ORGANIZATION_ENDPOINT
        )
        return OrganizationHttpResponse(**data).organization

    def update(self, *, name: str) -> Organization:
        body = UpdateOrganizationRequest(name=name).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = self._api.send_request(
            HttpMethods.PUT,
            Endpoints.ORGANIZATION_ENDPOINT,
            body=body,
        )
        return OrganizationHttpResponse(**data).organization

    async def a_get(self) -> Organization:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET, Endpoints.ORGANIZATION_ENDPOINT
        )
        return OrganizationHttpResponse(**data).organization

    async def a_update(self, *, name: str) -> Organization:
        body = UpdateOrganizationRequest(name=name).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = await self._api.a_send_request(
            HttpMethods.PUT,
            Endpoints.ORGANIZATION_ENDPOINT,
            body=body,
        )
        return OrganizationHttpResponse(**data).organization
