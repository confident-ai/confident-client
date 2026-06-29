from ...api import Api
from .permissions import OrganizationPermissions
from .policies import OrganizationPolicies
from .roles import OrganizationRoles


class OrganizationIam:
    def __init__(self, api: Api) -> None:
        self.policies = OrganizationPolicies(api)
        self.roles = OrganizationRoles(api)
        self.permissions = OrganizationPermissions(api)
