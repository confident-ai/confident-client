def test_projects_list(client, http):
    http.enqueue_data(
        {"projects": [{"id": "p1", "name": "Prod", "organizationId": "org_1"}]}
    )
    projects = client.projects.list()
    assert projects[0].id == "p1"
    assert projects[0].organization_id == "org_1"
    assert http.last["method"] == "GET"
    assert http.last["url"].endswith("/v1/projects")


def test_projects_create_returns_project_and_api_key(client, http):
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
    created = client.projects.create("New", description="desc")
    assert created.project.id == "p1"
    assert created.api_key.value == "confident_proj_secret"
    assert http.last["json"] == {
        "name": "New",
        "description": "desc",
    }


def test_project_client_scopes_project_id(client):
    project = client.project("proj_123")
    assert project.project_id == "proj_123"


def test_project_get(client, http):
    http.enqueue_data({"project": {"id": "proj_123", "name": "Prod"}})
    project = client.project("proj_123").get()
    assert project.id == "proj_123"
    assert http.last["url"].endswith("/v1/projects/proj_123")


def test_project_update_and_delete(client, http):
    http.enqueue_data({"project": {"id": "proj_123", "name": "Renamed"}})
    project = client.project("proj_123").update(name="Renamed")
    assert project.name == "Renamed"
    assert http.last["method"] == "PUT"
    assert http.last["json"] == {"name": "Renamed"}

    http.enqueue_data({"id": "proj_123", "deleted": True})
    result = client.project("proj_123").delete()
    assert result.deleted is True
    assert http.last["method"] == "DELETE"
    assert http.last["url"].endswith("/v1/projects/proj_123")


def test_project_api_keys_scoped_path(client, http):
    http.enqueue_data({"apiKeys": []})
    client.project("proj_123").api_keys.list()
    assert http.last["url"].endswith("/v1/projects/proj_123/api-keys")


def test_project_invitations_use_project_role_id(client, http):
    http.enqueue_data({"invitations": []})
    client.project("proj_123").invitations.create(
        ["e@f.com"], role_id="prole_1"
    )
    assert http.last["json"] == {
        "emails": ["e@f.com"],
        "projectRoleId": "prole_1",
    }
    assert http.last["url"].endswith("/v1/projects/proj_123/invitations")


def test_project_member_returns_project_role(client, http):
    http.enqueue_data(
        {
            "member": {
                "id": "u1",
                "email": "a@b.com",
                "projectRole": {"id": "prole_1", "name": "Owner"},
            }
        }
    )
    member = client.project("proj_123").members.update_role(
        "u1", role_id="prole_1"
    )
    assert member.project_role.name == "Owner"
