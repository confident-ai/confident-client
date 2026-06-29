"""Async method tests.

These mirror the sync suites but exercise the ``a_``-prefixed async methods on
the same ``ConfidentAI`` client (deepeval-style: one class exposes both ``foo``
and ``a_foo``). The async network seam (``Api._a_http_request``) is patched onto
the same ``RequestRecorder`` as the sync seam (see ``conftest.py``), so the
canned responses and request assertions are identical to the sync tests.
Coroutines are driven with ``asyncio.run`` to avoid a pytest-asyncio dependency.
"""

import asyncio

import pytest

from confidentai import ConfidentAI
from confidentai.types import ConfidentApiError


def run(coro):
    return asyncio.run(coro)


def test_factories_return_clients(async_client):
    from confidentai.organization import OrganizationClient
    from confidentai.projects import ProjectClient

    assert isinstance(async_client.organization(), OrganizationClient)
    project = async_client.project("proj_123")
    assert isinstance(project, ProjectClient)
    assert project.project_id == "proj_123"


def test_client_constructs():
    client = ConfidentAI(api_key="confident_us_org_abc")
    assert client.api_key == "confident_us_org_abc"


def test_whoami(async_client, http):
    http.enqueue_data({"organization": {"id": "org_1", "name": "Acme"}})
    org = run(async_client.a_whoami())
    assert org.id == "org_1"
    assert org.name == "Acme"
    assert http.last["method"] == "GET"
    assert http.last["url"].endswith("/v1/organization")


def test_organization_update(async_client, http):
    http.enqueue_data({"organization": {"id": "org_1", "name": "New"}})
    org = run(async_client.organization().a_update(name="New"))
    assert org.name == "New"
    assert http.last["method"] == "PUT"
    assert http.last["json"] == {"name": "New"}


def test_org_api_keys_lifecycle(async_client, http):
    org = async_client.organization()

    http.enqueue_data(
        {"apiKeys": [{"id": 1, "valid": True, "value": "***abc"}]}
    )
    keys = run(org.api_keys.a_list())
    assert keys[0].id == 1
    assert http.last["url"].endswith("/v1/organization/api-keys")

    http.enqueue_data(
        {"apiKey": {"id": 2, "name": "CI", "valid": True, "value": "secret"}}
    )
    created = run(org.api_keys.a_create(name="CI"))
    assert created.value == "secret"
    assert http.last["method"] == "POST"
    assert http.last["json"] == {"name": "CI"}

    http.enqueue_data(
        {"apiKey": {"id": 2, "name": "CI", "valid": False, "value": "***xyz"}}
    )
    updated = run(org.api_keys.a_update(2, valid=False))
    assert updated.valid is False
    assert http.last["method"] == "PUT"
    assert http.last["url"].endswith("/v1/organization/api-keys/2")

    http.enqueue_data({"id": 2, "deleted": True})
    deleted = run(org.api_keys.a_delete(2))
    assert deleted.deleted is True
    assert http.last["method"] == "DELETE"


def test_org_members_list_passes_pagination(async_client, http):
    http.enqueue_data({"members": [], "total": 0})
    run(async_client.organization().members.a_list(page=2, page_size=50))
    assert http.last["params"] == {"page": 2, "pageSize": 50}


def test_org_member_update_role(async_client, http):
    http.enqueue_data(
        {
            "member": {
                "id": "user_1",
                "email": "a@b.com",
                "organizationRole": {"id": "role_1", "name": "Admin"},
            }
        }
    )
    member = run(
        async_client.organization().members.a_update_role(
            "user_1", role_id="role_1"
        )
    )
    assert member.organization_role.name == "Admin"
    assert http.last["json"] == {"roleId": "role_1"}
    assert http.last["url"].endswith("/v1/organization/members/user_1")


def test_org_invitations_create(async_client, http):
    http.enqueue_data(
        {"invitations": [{"id": 1, "email": "c@d.com", "status": "PENDING"}]}
    )
    invites = run(
        async_client.organization().invitations.a_create(
            ["c@d.com"], role_id="role_2"
        )
    )
    assert invites[0].email == "c@d.com"
    assert http.last["json"] == {
        "emails": ["c@d.com"],
        "organizationRoleId": "role_2",
    }


def test_org_roles_create(async_client, http):
    http.enqueue_data({"role": {"id": "r1", "name": "Analyst", "policies": []}})
    role = run(
        async_client.organization().iam.roles.a_create(
            "Analyst", policy_ids=["p1"]
        )
    )
    assert role.name == "Analyst"
    assert http.last["json"] == {"name": "Analyst", "policyIds": ["p1"]}


def test_org_permissions_list(async_client, http):
    http.enqueue_data(
        {"permissions": [{"id": "perm1", "name": "billing:read"}]}
    )
    perms = run(async_client.organization().iam.permissions.a_list())
    assert perms[0].name == "billing:read"
    assert http.last["url"].endswith("/v1/organization/permissions")


def test_org_governance_policies_list(async_client, http):
    http.enqueue_data(
        {
            "governancePolicies": [
                {
                    "id": "gp1",
                    "name": "Production Gate",
                    "projectsCount": 5,
                    "controls": [
                        {
                            "id": "c1",
                            "name": "Logs traces",
                            "type": "PRE_DEPLOYMENT_EVALS",
                        }
                    ],
                }
            ]
        }
    )
    policies = run(async_client.organization().governance.policies.a_list())
    assert policies[0].id == "gp1"
    assert policies[0].projects_count == 5
    assert policies[0].controls[0].type == "PRE_DEPLOYMENT_EVALS"
    assert http.last["url"].endswith("/v1/organization/governance-policies")


def test_org_governance_policies_list_projects(async_client, http):
    http.enqueue_data({"projects": [{"id": "p1", "name": "Prod"}], "total": 1})
    projects = run(
        async_client.organization().governance.policies.a_list_projects(
            "gp1", page=2, page_size=50
        )
    )
    assert projects[0].id == "p1"
    assert http.last["params"] == {"page": 2, "pageSize": 50}
    assert http.last["url"].endswith(
        "/v1/organization/governance-policies/gp1/projects"
    )


def test_org_governance_policies_assign(async_client, http):
    http.enqueue_data(
        {
            "governancePolicy": {"id": "gp1", "name": "Production Gate"},
            "assignedProjectIds": ["p1", "p2"],
            "notFoundProjectIds": [],
            "count": 2,
        }
    )
    result = run(
        async_client.organization().governance.policies.a_assign(
            "gp1", project_ids=["p1", "p2"]
        )
    )
    assert result.assigned_project_ids == ["p1", "p2"]
    assert result.not_found_project_ids == []
    assert result.count == 2
    assert http.last["method"] == "POST"
    assert http.last["json"] == {"projectIds": ["p1", "p2"]}
    assert http.last["url"].endswith(
        "/v1/organization/governance-policies/gp1/assign"
    )


def test_org_governance_policies_unassign(async_client, http):
    http.enqueue_data(
        {
            "governancePolicy": {"id": "gp1", "name": "Production Gate"},
            "unassignedProjectIds": ["p1"],
            "skippedProjectIds": [],
            "count": 1,
        }
    )
    result = run(
        async_client.organization().governance.policies.a_unassign(
            "gp1", project_ids=["p1"]
        )
    )
    assert result.unassigned_project_ids == ["p1"]
    assert result.skipped_project_ids == []
    assert result.count == 1
    assert http.last["url"].endswith(
        "/v1/organization/governance-policies/gp1/unassign"
    )


def test_projects_list(async_client, http):
    http.enqueue_data(
        {"projects": [{"id": "p1", "name": "Prod", "organizationId": "org_1"}]}
    )
    projects = run(async_client.projects.a_list())
    assert projects[0].id == "p1"
    assert projects[0].organization_id == "org_1"
    assert http.last["method"] == "GET"
    assert http.last["url"].endswith("/v1/projects")


def test_projects_create(async_client, http):
    http.enqueue_data(
        {
            "project": {"id": "p1", "name": "New"},
            "apiKey": {
                "id": 7,
                "name": "Default Key",
                "valid": True,
                "value": "confident_proj_secret",
            },
        }
    )
    created = run(async_client.projects.a_create("New", description="desc"))
    assert created.project.id == "p1"
    assert created.api_key.value == "confident_proj_secret"
    assert http.last["json"] == {"name": "New", "description": "desc"}


def test_project_get_update_delete(async_client, http):
    http.enqueue_data({"project": {"id": "proj_123", "name": "Prod"}})
    project = run(async_client.project("proj_123").a_get())
    assert project.id == "proj_123"
    assert http.last["url"].endswith("/v1/projects/proj_123")

    http.enqueue_data({"project": {"id": "proj_123", "name": "Renamed"}})
    updated = run(async_client.project("proj_123").a_update(name="Renamed"))
    assert updated.name == "Renamed"
    assert http.last["method"] == "PUT"
    assert http.last["json"] == {"name": "Renamed"}

    http.enqueue_data({"id": "proj_123", "deleted": True})
    result = run(async_client.project("proj_123").a_delete())
    assert result.deleted is True
    assert http.last["method"] == "DELETE"


def test_project_api_keys_scoped_path(async_client, http):
    http.enqueue_data({"apiKeys": []})
    run(async_client.project("proj_123").api_keys.a_list())
    assert http.last["url"].endswith("/v1/projects/proj_123/api-keys")


def test_project_invitations_use_project_role_id(async_client, http):
    http.enqueue_data({"invitations": []})
    run(
        async_client.project("proj_123").invitations.a_create(
            ["e@f.com"], role_id="prole_1"
        )
    )
    assert http.last["json"] == {
        "emails": ["e@f.com"],
        "projectRoleId": "prole_1",
    }
    assert http.last["url"].endswith("/v1/projects/proj_123/invitations")


def test_error_envelope_raises_confident_api_error(async_client, http):
    http.enqueue_raw({"success": False, "error": "boom"})
    with pytest.raises(ConfidentApiError) as excinfo:
        run(async_client.a_whoami())
    assert str(excinfo.value) == "boom"
