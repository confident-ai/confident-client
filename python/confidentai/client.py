from typing import Optional

from .api import Api
from .organization import OrganizationClient
from .projects import ProjectClient, ProjectsClient
from .types import Organization


class ConfidentAI:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self._api = Api(api_key=api_key, base_url=base_url, timeout=timeout)
        self.api_key = self._api.api_key
        self.base_url = self._api.base_url
        self.projects = ProjectsClient(self._api)

    def organization(self) -> OrganizationClient:
        return OrganizationClient(self._api)

    def project(self, project_id: str) -> ProjectClient:
        return ProjectClient(self._api, project_id)

    def whoami(self) -> Organization:
        return self.organization().get()

    async def a_whoami(self) -> Organization:
        return await self.organization().a_get()
