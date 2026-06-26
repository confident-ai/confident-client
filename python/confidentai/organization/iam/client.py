from ...api import Api
from .permissions import AsyncOrganizationPermissions, OrganizationPermissions
from .policies import AsyncOrganizationPolicies, OrganizationPolicies
from .roles import AsyncOrganizationRoles, OrganizationRoles


class OrganizationIam:
    def __init__(self, api: Api) -> None:
        self.policies = OrganizationPolicies(api)
        self.roles = OrganizationRoles(api)
        self.permissions = OrganizationPermissions(api)


class AsyncOrganizationIam:
    def __init__(self, api: Api) -> None:
        self.policies = AsyncOrganizationPolicies(api)
        self.roles = AsyncOrganizationRoles(api)
        self.permissions = AsyncOrganizationPermissions(api)
