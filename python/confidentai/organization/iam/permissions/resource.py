from typing import List

from ....api import Api, Endpoints, HttpMethods
from ....types import Permission
from .types import PermissionsHttpResponse


class OrganizationPermissions:
    def __init__(self, api: Api) -> None:
        self._api = api

    def list(self) -> List[Permission]:
        data, _ = self._api.send_request(
            HttpMethods.GET, Endpoints.ORGANIZATION_PERMISSIONS_ENDPOINT
        )
        return PermissionsHttpResponse(**data).permissions

    async def a_list(self) -> List[Permission]:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET, Endpoints.ORGANIZATION_PERMISSIONS_ENDPOINT
        )
        return PermissionsHttpResponse(**data).permissions
