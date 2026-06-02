import pytest
import requests

from confidentai.api import Api, Endpoints, HttpMethods
from confidentai.types import ConfidentApiError


@pytest.fixture
def api():
    return Api(api_key="confident_us_org_k", base_url="https://api.test")


def test_sets_auth_and_version_headers(api, http):
    http.enqueue_data({"ok": True})
    api.send_request(HttpMethods.GET, Endpoints.ORGANIZATION_ENDPOINT)
    headers = http.last["headers"]
    assert headers["CONFIDENT_API_KEY"] == "confident_us_org_k"
    assert headers["Content-Type"] == "application/json"
    assert headers["X-Confident-SDK-Version"].startswith("confidentai-python/")


def test_get_unwraps_data_envelope(api, http):
    http.enqueue_data({"value": 42})
    result, link = api.send_request(
        HttpMethods.GET, Endpoints.ORGANIZATION_ENDPOINT
    )
    assert result == {"value": 42}
    assert link is None


def test_post_serializes_json_body(api, http):
    http.enqueue_data({})
    api.send_request(
        HttpMethods.PUT, Endpoints.ORGANIZATION_ENDPOINT, body={"name": "Acme"}
    )
    assert http.last["json"] == {"name": "Acme"}
    assert http.last["method"] == "PUT"


def test_none_query_params_are_dropped(api, http):
    http.enqueue_data({})
    api.send_request(
        HttpMethods.GET,
        Endpoints.ORGANIZATION_MEMBERS_ENDPOINT,
        params={"page": 1, "pageSize": None},
    )
    assert http.last["params"] == {"page": 1}


def test_url_params_substitute_placeholders(api, http):
    http.enqueue_data({})
    api.send_request(
        HttpMethods.DELETE,
        Endpoints.PROJECT_API_KEY_ENDPOINT,
        url_params={"projectId": "p1", "apiKeyId": 42},
    )
    assert http.last["url"].endswith("/v1/projects/p1/api-keys/42")
    assert ":projectId" not in http.last["url"]
    assert ":apiKeyId" not in http.last["url"]


@pytest.mark.parametrize("status_code", [400, 401, 403, 404, 422, 429, 500])
def test_unsuccessful_response_raises_confident_api_error(
    api, http, status_code
):
    http.enqueue_raw(
        {"success": False, "error": "boom"}, status_code=status_code
    )
    with pytest.raises(ConfidentApiError) as exc:
        api.send_request(HttpMethods.GET, Endpoints.ORGANIZATION_ENDPOINT)
    assert str(exc.value) == "boom"


def test_success_false_with_200_raises_confident_api_error(api, http):
    http.enqueue_raw({"success": False, "error": "nope"}, status_code=200)
    with pytest.raises(ConfidentApiError) as exc:
        api.send_request(HttpMethods.GET, Endpoints.ORGANIZATION_ENDPOINT)
    assert str(exc.value) == "nope"


def test_error_link_is_preserved(api, http):
    http.enqueue_raw(
        {"success": False, "error": "gone", "link": "https://x"},
        status_code=404,
    )
    with pytest.raises(ConfidentApiError) as exc:
        api.send_request(HttpMethods.GET, Endpoints.ORGANIZATION_ENDPOINT)
    assert exc.value.link == "https://x"


def test_connection_error_propagates(api, monkeypatch):
    def boom(*args, **kwargs):
        raise requests.ConnectionError("dns fail")

    monkeypatch.setattr(Api, "_http_request", staticmethod(boom))
    with pytest.raises(requests.ConnectionError):
        api.send_request(HttpMethods.GET, Endpoints.ORGANIZATION_ENDPOINT)
