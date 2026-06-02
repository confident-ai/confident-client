import pytest

from confidentai import ConfidentAI
from confidentai.api import (
    API_BASE_URL,
    API_BASE_URL_EU,
)


def test_initializes_with_explicit_api_key():
    client = ConfidentAI(api_key="confident_us_org_abc")
    assert client.api_key == "confident_us_org_abc"
    assert client.base_url == API_BASE_URL


def test_initializes_from_env_var(monkeypatch):
    monkeypatch.setenv("CONFIDENT_ORG_API_KEY", "confident_us_org_fromenv")
    client = ConfidentAI()
    assert client.api_key == "confident_us_org_fromenv"


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("CONFIDENT_ORG_API_KEY", raising=False)
    with pytest.raises(ValueError):
        ConfidentAI()


def test_base_url_override():
    client = ConfidentAI(api_key="k", base_url="https://example.test/api/")
    assert client.base_url == "https://example.test/api"


def test_base_url_from_env(monkeypatch):
    monkeypatch.setenv("CONFIDENT_BASE_URL", "https://from-env.test")
    client = ConfidentAI(api_key="k")
    assert client.base_url == "https://from-env.test"


def test_region_env_selects_base_url(monkeypatch):
    monkeypatch.delenv("CONFIDENT_BASE_URL", raising=False)
    monkeypatch.setenv("CONFIDENT_REGION", "EU")
    client = ConfidentAI(api_key="k")
    assert client.base_url == API_BASE_URL_EU


def test_region_inferred_from_api_key_prefix(monkeypatch):
    monkeypatch.delenv("CONFIDENT_BASE_URL", raising=False)
    monkeypatch.delenv("CONFIDENT_REGION", raising=False)
    client = ConfidentAI(api_key="confident_eu_org_xyz")
    assert client.base_url == API_BASE_URL_EU


def test_timeout_override():
    client = ConfidentAI(api_key="k", timeout=5.0)
    assert client._api.timeout == 5.0


def test_organization_and_project_factories(client):
    from confidentai.organization import OrganizationClient
    from confidentai.projects import ProjectClient

    assert isinstance(client.organization(), OrganizationClient)
    project = client.project("proj_123")
    assert isinstance(project, ProjectClient)
    assert project.project_id == "proj_123"


def test_whoami_returns_organization(client, http):
    http.enqueue_data({"organization": {"id": "org_1", "name": "Acme"}})
    org = client.whoami()
    assert org.id == "org_1"
    assert org.name == "Acme"
    assert http.last["url"].endswith("/v1/organization")
    assert http.last["method"] == "GET"
