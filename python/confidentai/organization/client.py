from ..api import Api, Endpoints, HttpMethods
from ..types import Organization
from .api_keys import AsyncOrganizationApiKeys, OrganizationApiKeys
from .invitations import AsyncOrganizationInvitations, OrganizationInvitations
from .members import AsyncOrganizationMembers, OrganizationMembers
from .permissions import AsyncOrganizationPermissions, OrganizationPermissions
from .policies import AsyncOrganizationPolicies, OrganizationPolicies
from .roles import AsyncOrganizationRoles, OrganizationRoles
from .types import OrganizationHttpResponse, UpdateOrganizationRequest


class OrganizationClient:
    def __init__(self, api: Api) -> None:
        self._api = api
        self.api_keys = OrganizationApiKeys(api)
        self.members = OrganizationMembers(api)
        self.invitations = OrganizationInvitations(api)
        self.roles = OrganizationRoles(api)
        self.policies = OrganizationPolicies(api)
        self.permissions = OrganizationPermissions(api)

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


class AsyncOrganizationClient:
    def __init__(self, api: Api) -> None:
        self._api = api
        self.api_keys = AsyncOrganizationApiKeys(api)
        self.members = AsyncOrganizationMembers(api)
        self.invitations = AsyncOrganizationInvitations(api)
        self.roles = AsyncOrganizationRoles(api)
        self.policies = AsyncOrganizationPolicies(api)
        self.permissions = AsyncOrganizationPermissions(api)

    async def get(self) -> Organization:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET, Endpoints.ORGANIZATION_ENDPOINT
        )
        return OrganizationHttpResponse(**data).organization

    async def update(self, *, name: str) -> Organization:
        body = UpdateOrganizationRequest(name=name).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = await self._api.a_send_request(
            HttpMethods.PUT,
            Endpoints.ORGANIZATION_ENDPOINT,
            body=body,
        )
        return OrganizationHttpResponse(**data).organization
