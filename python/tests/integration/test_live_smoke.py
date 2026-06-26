"""Live integration tests against the real Confident AI API.

These are excluded from the default unit gate and only run when
``CONFIDENT_ORG_API_KEY`` is set. Run them explicitly with:

    CONFIDENT_ORG_API_KEY="confident_org_..." poetry run pytest -m integration

The read-only checks are always safe. The create/get/delete round-trip writes
to your organization but cleans up after itself via ``try/finally``.
"""

import time
import uuid

import pytest

from confidentai import ConfidentApiError

pytestmark = pytest.mark.integration


def test_whoami_returns_organization(live_client):
    org = live_client.whoami()
    assert org.id
    assert org.name


def test_projects_list_is_iterable(live_client):
    projects = live_client.projects.list()
    assert isinstance(projects, list)


def test_organization_permissions_list(live_client):
    permissions = live_client.organization().iam.permissions.list()
    assert isinstance(permissions, list)


def test_governance_policies_list_is_iterable(live_client):
    policies = live_client.organization().governance.policies.list()
    assert isinstance(policies, list)


def test_project_create_get_delete_round_trip(live_client):
    name = f"confidentai-sdk-itest-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    created = live_client.projects.create(
        name=name,
        description="Created by the confidentai SDK integration suite; safe to delete.",
    )
    project_id = created.project.id
    try:
        assert created.project.name == name

        fetched = live_client.project(project_id).get()
        assert fetched.id == project_id

        listed_ids = {p.id for p in live_client.projects.list()}
        assert project_id in listed_ids
    finally:
        result = live_client.project(project_id).delete()
        assert result.deleted or result.id == project_id


def test_unknown_project_raises(live_client):
    with pytest.raises(ConfidentApiError):
        live_client.project("does-not-exist-xxxxxxxx").get()
