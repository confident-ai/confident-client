import json as _json
import logging
import math
import os
from enum import Enum
from typing import Any, Mapping, Optional, Tuple, Union

import aiohttp
import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    wait_exponential_jitter,
    RetryCallState,
)

from ._version import __version__
from .types import ApiResponse, ConfidentApiError
from .utils.request import drop_none, join_url

CONFIDENT_ORG_API_KEY_ENV_VAR = "CONFIDENT_ORG_API_KEY"
CONFIDENT_BASE_URL_ENV_VAR = "CONFIDENT_BASE_URL"
CONFIDENT_REGION_ENV_VAR = "CONFIDENT_REGION"

API_BASE_URL = "https://api.confident-ai.com"
API_BASE_URL_EU = "https://eu.api.confident-ai.com"

API_KEY_HEADER = "CONFIDENT_API_KEY"
SDK_VERSION_HEADER = "X-Confident-SDK-Version"

DEFAULT_TIMEOUT = 30.0

retryable_exceptions = requests.exceptions.SSLError
async_retryable_exceptions = (
    aiohttp.ClientConnectionError,
    aiohttp.ClientSSLError,
)


def _infer_region_from_api_key(api_key: Optional[str]) -> Optional[str]:
    if not api_key:
        return None
    key = api_key.strip().lower()
    if key.startswith("confident_eu_"):
        return "EU"
    if key.startswith("confident_us_"):
        return "US"
    return None


def get_confident_api_key(api_key: Optional[str] = None) -> Optional[str]:
    if api_key:
        return api_key
    return os.getenv(CONFIDENT_ORG_API_KEY_ENV_VAR) or None


def get_base_api_url(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> str:
    if base_url:
        return base_url.rstrip("/")

    env_base_url = os.getenv(CONFIDENT_BASE_URL_ENV_VAR)
    if env_base_url:
        return env_base_url.rstrip("/")

    region = os.getenv(CONFIDENT_REGION_ENV_VAR) or _infer_region_from_api_key(
        api_key
    )
    region = (region or "US").upper()
    if region == "EU":
        return API_BASE_URL_EU
    return API_BASE_URL


def log_retry_error(retry_state: RetryCallState):
    exception = retry_state.outcome.exception()
    logging.error(
        f"Confident AI Error: {exception}. Retrying: {retry_state.attempt_number} time(s)..."
    )


class HttpMethods(Enum):
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"
    PUT = "PUT"


class Endpoints(Enum):
    # Organization management
    ORGANIZATION_ENDPOINT = "/v1/organization"
    ORGANIZATION_MEMBERS_ENDPOINT = "/v1/organization/members"
    ORGANIZATION_MEMBER_ENDPOINT = "/v1/organization/members/:userId"
    ORGANIZATION_INVITATIONS_ENDPOINT = "/v1/organization/invitations"
    ORGANIZATION_INVITATION_ENDPOINT = (
        "/v1/organization/invitations/:invitationId"
    )
    ORGANIZATION_ROLES_ENDPOINT = "/v1/organization/roles"
    ORGANIZATION_ROLE_ENDPOINT = "/v1/organization/roles/:roleId"
    ORGANIZATION_POLICIES_ENDPOINT = "/v1/organization/policies"
    ORGANIZATION_POLICY_ENDPOINT = "/v1/organization/policies/:policyId"
    ORGANIZATION_PERMISSIONS_ENDPOINT = "/v1/organization/permissions"
    ORGANIZATION_API_KEYS_ENDPOINT = "/v1/organization/api-keys"
    ORGANIZATION_API_KEY_ENDPOINT = "/v1/organization/api-keys/:apiKeyId"

    # Project management
    PROJECTS_ENDPOINT = "/v1/projects"
    PROJECT_ENDPOINT = "/v1/projects/:projectId"
    PROJECT_MEMBERS_ENDPOINT = "/v1/projects/:projectId/members"
    PROJECT_MEMBER_ENDPOINT = "/v1/projects/:projectId/members/:userId"
    PROJECT_INVITATIONS_ENDPOINT = "/v1/projects/:projectId/invitations"
    PROJECT_INVITATION_ENDPOINT = (
        "/v1/projects/:projectId/invitations/:invitationId"
    )
    PROJECT_ROLES_ENDPOINT = "/v1/projects/:projectId/roles"
    PROJECT_ROLE_ENDPOINT = "/v1/projects/:projectId/roles/:roleId"
    PROJECT_POLICIES_ENDPOINT = "/v1/projects/:projectId/policies"
    PROJECT_POLICY_ENDPOINT = "/v1/projects/:projectId/policies/:policyId"
    PROJECT_PERMISSIONS_ENDPOINT = "/v1/projects/:projectId/permissions"
    PROJECT_API_KEYS_ENDPOINT = "/v1/projects/:projectId/api-keys"
    PROJECT_API_KEY_ENDPOINT = "/v1/projects/:projectId/api-keys/:apiKeyId"


def _sanitize_body(obj):
    """Recursively replace non-finite floats (NaN, Inf, -Inf) with None."""
    if isinstance(obj, float):
        return None if not math.isfinite(obj) else obj
    if isinstance(obj, dict):
        return {k: _sanitize_body(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_body(v) for v in obj]
    return obj


class _AsyncResponse:
    """Response shim so ``a_send_request`` can reuse the sync handling path.

    Mirrors the parts of ``requests.Response`` that the response handling
    relies on: ``status_code``, ``json()`` (raising ``ValueError`` on a
    non-JSON body, like ``requests`` does), and ``text``.
    """

    def __init__(self, status_code: int, text: str) -> None:
        self.status_code = status_code
        self.text = text

    def json(self) -> Any:
        return _json.loads(self.text)


class Api:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        api_key = get_confident_api_key(api_key)
        if not api_key:
            raise ValueError(
                f"No Confident API key found. Please set the {CONFIDENT_ORG_API_KEY_ENV_VAR} environment variable or pass api_key."
            )

        self.api_key = api_key
        self.base_url = get_base_api_url(api_key, base_url)
        self.timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
        self._headers = {
            "Content-Type": "application/json",
            API_KEY_HEADER: api_key,
            SDK_VERSION_HEADER: f"confidentai-python/{__version__}",
        }

    @staticmethod
    @retry(
        wait=wait_exponential_jitter(initial=1, exp_base=2, jitter=2, max=10),
        retry=retry_if_exception_type(retryable_exceptions),
        after=log_retry_error,
    )
    def _http_request(
        method: str,
        url: str,
        headers: Mapping[str, str],
        params: Optional[Mapping[str, Any]],
        json: Optional[Any],
        timeout: float,
    ) -> requests.Response:
        session = requests.Session()
        return session.request(
            method=method,
            url=url,
            headers=dict(headers),
            params=params,
            json=json,
            timeout=timeout,
            verify=True,
        )

    def _handle_response(
        self, response_data: Union[dict, Any]
    ) -> Tuple[Any, Optional[str]]:
        if not isinstance(response_data, dict):
            return response_data, None

        try:
            api_response = ApiResponse(**response_data)
        except Exception:
            return response_data, None

        if api_response.deprecated:
            deprecation_msg = "You are using a deprecated API endpoint. Please update your confidentai version."
            if api_response.link:
                deprecation_msg += f" See: {api_response.link}"
            logging.warning(deprecation_msg)

        if not api_response.success:
            error_message = api_response.error or "Request failed"
            raise ConfidentApiError(error_message, api_response.link)

        return api_response.data, api_response.link

    def send_request(
        self,
        method: HttpMethods,
        endpoint: Endpoints,
        body=None,
        params=None,
        url_params=None,
    ) -> Tuple[Any, Optional[str]]:
        path = endpoint.value
        if url_params:
            for key, value in url_params.items():
                path = path.replace(f":{key}", str(value))

        url = join_url(self.base_url, path)
        if body is not None:
            body = _sanitize_body(body)

        res = self._http_request(
            method.value,
            url,
            self._headers,
            drop_none(params),
            body,
            self.timeout,
        )

        if res.status_code == 200:
            try:
                response_data = res.json()
                return self._handle_response(response_data)
            except ValueError:
                return res.text, None
        else:
            try:
                error_data = res.json()
                return self._handle_response(error_data)
            except (ValueError, ConfidentApiError) as e:
                if isinstance(e, ConfidentApiError):
                    raise e
                error_message = (
                    error_data.get("error", res.text)
                    if "error_data" in locals()
                    else res.text
                )
                raise Exception(error_message)

    @staticmethod
    @retry(
        wait=wait_exponential_jitter(initial=1, exp_base=2, jitter=2, max=10),
        retry=retry_if_exception_type(async_retryable_exceptions),
        after=log_retry_error,
    )
    async def _a_http_request(
        method: str,
        url: str,
        headers: Mapping[str, str],
        params: Optional[Mapping[str, Any]],
        json: Optional[Any],
        timeout: float,
    ) -> _AsyncResponse:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=dict(headers),
                json=json,
                params=params,
                ssl=True,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as res:
                return _AsyncResponse(res.status, await res.text())

    async def a_send_request(
        self,
        method: HttpMethods,
        endpoint: Endpoints,
        body=None,
        params=None,
        url_params=None,
    ) -> Tuple[Any, Optional[str]]:
        path = endpoint.value
        if url_params:
            for key, value in url_params.items():
                path = path.replace(f":{key}", str(value))

        url = join_url(self.base_url, path)
        if body is not None:
            body = _sanitize_body(body)

        res = await self._a_http_request(
            method.value,
            url,
            self._headers,
            drop_none(params),
            body,
            self.timeout,
        )

        if res.status_code == 200:
            try:
                response_data = res.json()
                return self._handle_response(response_data)
            except ValueError:
                return res.text, None
        else:
            try:
                error_data = res.json()
                return self._handle_response(error_data)
            except (ValueError, ConfidentApiError) as e:
                if isinstance(e, ConfidentApiError):
                    raise e
                error_message = (
                    error_data.get("error", res.text)
                    if "error_data" in locals()
                    else res.text
                )
                raise Exception(error_message)
