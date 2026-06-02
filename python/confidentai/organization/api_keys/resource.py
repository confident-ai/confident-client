from typing import List

from ...api import Api, Endpoints, HttpMethods
from ...types import ApiKey, DeletionResult
from .types import (
    ApiKeyHttpResponse,
    ApiKeysHttpResponse,
    CreateApiKeyRequest,
    UpdateApiKeyRequest,
)


class OrganizationApiKeys:
    def __init__(self, api: Api) -> None:
        self._api = api

    def list(self) -> List[ApiKey]:
        data, _ = self._api.send_request(
            HttpMethods.GET, Endpoints.ORGANIZATION_API_KEYS_ENDPOINT
        )
        return ApiKeysHttpResponse(**data).api_keys

    def get(self, api_key_id: int) -> ApiKey:
        data, _ = self._api.send_request(
            HttpMethods.GET,
            Endpoints.ORGANIZATION_API_KEY_ENDPOINT,
            url_params={"apiKeyId": api_key_id},
        )
        return ApiKeyHttpResponse(**data).api_key

    def create(self, name: str) -> ApiKey:
        body = CreateApiKeyRequest(name=name).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = self._api.send_request(
            HttpMethods.POST,
            Endpoints.ORGANIZATION_API_KEYS_ENDPOINT,
            body=body,
        )
        return ApiKeyHttpResponse(**data).api_key

    def update(self, api_key_id: int, *, valid: bool) -> ApiKey:
        body = UpdateApiKeyRequest(valid=valid).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = self._api.send_request(
            HttpMethods.PUT,
            Endpoints.ORGANIZATION_API_KEY_ENDPOINT,
            body=body,
            url_params={"apiKeyId": api_key_id},
        )
        return ApiKeyHttpResponse(**data).api_key

    def delete(self, api_key_id: int) -> DeletionResult:
        data, _ = self._api.send_request(
            HttpMethods.DELETE,
            Endpoints.ORGANIZATION_API_KEY_ENDPOINT,
            url_params={"apiKeyId": api_key_id},
        )
        return DeletionResult(**data)


class AsyncOrganizationApiKeys:
    def __init__(self, api: Api) -> None:
        self._api = api

    async def list(self) -> List[ApiKey]:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET, Endpoints.ORGANIZATION_API_KEYS_ENDPOINT
        )
        return ApiKeysHttpResponse(**data).api_keys

    async def get(self, api_key_id: int) -> ApiKey:
        data, _ = await self._api.a_send_request(
            HttpMethods.GET,
            Endpoints.ORGANIZATION_API_KEY_ENDPOINT,
            url_params={"apiKeyId": api_key_id},
        )
        return ApiKeyHttpResponse(**data).api_key

    async def create(self, name: str) -> ApiKey:
        body = CreateApiKeyRequest(name=name).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = await self._api.a_send_request(
            HttpMethods.POST,
            Endpoints.ORGANIZATION_API_KEYS_ENDPOINT,
            body=body,
        )
        return ApiKeyHttpResponse(**data).api_key

    async def update(self, api_key_id: int, *, valid: bool) -> ApiKey:
        body = UpdateApiKeyRequest(valid=valid).model_dump(
            by_alias=True, exclude_none=True
        )
        data, _ = await self._api.a_send_request(
            HttpMethods.PUT,
            Endpoints.ORGANIZATION_API_KEY_ENDPOINT,
            body=body,
            url_params={"apiKeyId": api_key_id},
        )
        return ApiKeyHttpResponse(**data).api_key

    async def delete(self, api_key_id: int) -> DeletionResult:
        data, _ = await self._api.a_send_request(
            HttpMethods.DELETE,
            Endpoints.ORGANIZATION_API_KEY_ENDPOINT,
            url_params={"apiKeyId": api_key_id},
        )
        return DeletionResult(**data)
