from ...api import Api
from .policies import AsyncGovernancePolicies, GovernancePolicies


class OrganizationGovernance:
    def __init__(self, api: Api) -> None:
        self.policies = GovernancePolicies(api)


class AsyncOrganizationGovernance:
    def __init__(self, api: Api) -> None:
        self.policies = AsyncGovernancePolicies(api)
