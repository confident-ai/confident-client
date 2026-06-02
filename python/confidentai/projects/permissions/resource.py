from typing import List

from ...api import Api, Endpoints, HttpMethods
from ...types import Permission
from .types import PermissionsHttpResponse


class ProjectPermissions:
    def __init__(self, api: Api, project_id: str) -> None:
        self._api = api
        self._project_id = project_id

    def list(self) -> List[Permission]:
        data, _ = self._api.send_request(
            HttpMethods.GET,
            Endpoints.PROJECT_PERMISSIONS_ENDPOINT,
            url_params={"projectId": self._project_id},
        )
        return PermissionsHttpResponse(**data).permissions


class AsyncProjectPermissions:
    def __init__(self, api: Api, project_id: str) -> None:
        self._api = api
        self._project_id = project_id

    async def list(self) -> List[Permission]:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET,
            Endpoints.PROJECT_PERMISSIONS_ENDPOINT,
            url_params={"projectId": self._project_id},
        )
        return PermissionsHttpResponse(**data).permissions
