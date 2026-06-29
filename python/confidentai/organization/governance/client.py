from ...api import Api
from .policies import OrganizationGovernancePolicies


class OrganizationGovernance:
    def __init__(self, api: Api) -> None:
        self.policies = OrganizationGovernancePolicies(api)
