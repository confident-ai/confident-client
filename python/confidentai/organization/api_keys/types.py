from typing import List

from pydantic import Field

from ...types import ApiKey, ConfidentBaseModel


class CreateApiKeyRequest(ConfidentBaseModel):
    name: str


class UpdateApiKeyRequest(ConfidentBaseModel):
    valid: bool


class ApiKeyHttpResponse(ConfidentBaseModel):
    api_key: ApiKey = Field(alias="apiKey")


class ApiKeysHttpResponse(ConfidentBaseModel):
    api_keys: List[ApiKey] = Field(default_factory=list, alias="apiKeys")
