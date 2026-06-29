from ...api import Api
from .policies import GovernancePolicies


class OrganizationGovernance:
    def __init__(self, api: Api) -> None:
        self.policies = GovernancePolicies(api)
