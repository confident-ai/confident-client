"""Shared pytest fixtures.

HTTP is mocked by monkeypatching the network seams (``Api._http_request`` for
the sync client and ``Api._a_http_request`` for the async client), so no test
ever hits a real API. Both seams share a single :class:`RequestRecorder`, so a
sync and async test asserting the same behavior read from the same queue.
"""

from typing import Any, Dict, List, Optional

import pytest

from confidentai.api import Api


class FakeResponse:
    def __init__(
        self,
        status_code: int = 200,
        payload: Any = None,
        text: str = "",
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self) -> Any:
        if self._payload is None:
            raise ValueError("No JSON body")
        return self._payload


class RequestRecorder:
    """Records outgoing requests and returns queued/canned responses."""

    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []
        self._queue: List[FakeResponse] = []

    def enqueue_data(
        self, data: Any, *, status_code: int = 200, success: bool = True
    ) -> None:
        self._queue.append(
            FakeResponse(status_code, {"success": success, "data": data})
        )

    def enqueue_raw(
        self, payload: Any, *, status_code: int = 200, text: str = ""
    ) -> None:
        self._queue.append(FakeResponse(status_code, payload, text))

    def _handle(
        self,
        method: str,
        url: str,
        headers: Any,
        params: Optional[Any],
        json: Optional[Any],
        timeout: float,
    ) -> FakeResponse:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers),
                "params": params,
                "json": json,
                "timeout": timeout,
            }
        )
        if self._queue:
            return self._queue.pop(0)
        return FakeResponse(200, {"success": True, "data": {}})

    @property
    def last(self) -> Dict[str, Any]:
        return self.calls[-1]


@pytest.fixture
def http(monkeypatch) -> RequestRecorder:
    recorder = RequestRecorder()

    def fake_http_request(method, url, headers, params, json, timeout):
        return recorder._handle(method, url, headers, params, json, timeout)

    async def fake_a_http_request(method, url, headers, params, json, timeout):
        return recorder._handle(method, url, headers, params, json, timeout)

    monkeypatch.setattr(Api, "_http_request", staticmethod(fake_http_request))
    monkeypatch.setattr(
        Api, "_a_http_request", staticmethod(fake_a_http_request)
    )
    return recorder


@pytest.fixture
def client(http):
    from confidentai import ConfidentAI

    return ConfidentAI(api_key="confident_us_org_testkey")


@pytest.fixture
def async_client(http):
    from confidentai import ConfidentAI

    return ConfidentAI(api_key="confident_us_org_testkey")
