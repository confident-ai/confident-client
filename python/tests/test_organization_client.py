def test_get_organization(client, http):
    http.enqueue_data(
        {"organization": {"id": "org_1", "name": "Acme", "plan": "PREMIUM"}}
    )
    org = client.organization().get()
    assert org.id == "org_1"
    assert org.plan == "PREMIUM"
    assert http.last["method"] == "GET"
    assert http.last["url"].endswith("/v1/organization")


def test_update_organization(client, http):
    http.enqueue_data({"organization": {"id": "org_1", "name": "New"}})
    org = client.organization().update(name="New")
    assert org.name == "New"
    assert http.last["method"] == "PUT"
    assert http.last["json"] == {"name": "New"}


def test_api_keys_lifecycle(client, http):
    org = client.organization()

    http.enqueue_data(
        {"apiKeys": [{"id": 1, "valid": True, "value": "***abc"}]}
    )
    keys = org.api_keys.list()
    assert keys[0].id == 1
    assert http.last["url"].endswith("/v1/organization/api-keys")

    http.enqueue_data(
        {"apiKey": {"id": 2, "name": "CI", "valid": True, "value": "secret"}}
    )
    created = org.api_keys.create(name="CI")
    assert created.value == "secret"
    assert http.last["method"] == "POST"
    assert http.last["json"] == {"name": "CI"}

    http.enqueue_data(
        {"apiKey": {"id": 2, "name": "CI", "valid": False, "value": "***xyz"}}
    )
    updated = org.api_keys.update(2, valid=False)
    assert updated.valid is False
    assert http.last["method"] == "PUT"
    assert http.last["json"] == {"valid": False}
    assert http.last["url"].endswith("/v1/organization/api-keys/2")

    http.enqueue_data({"id": 2, "deleted": True})
    deleted = org.api_keys.delete(2)
    assert deleted.deleted is True
    assert http.last["method"] == "DELETE"


def test_member_update_role_and_remove(client, http):
    org = client.organization()

    http.enqueue_data(
        {
            "member": {
                "id": "user_1",
                "email": "a@b.com",
                "organizationRole": {"id": "role_1", "name": "Admin"},
            }
        }
    )
    member = org.members.update_role("user_1", role_id="role_1")
    assert member.organization_role.name == "Admin"
    assert http.last["method"] == "PUT"
    assert http.last["json"] == {"roleId": "role_1"}
    assert http.last["url"].endswith("/v1/organization/members/user_1")

    http.enqueue_data({"id": "user_1", "removed": True})
    removed = org.members.remove("user_1")
    assert removed.removed is True


def test_members_list_passes_pagination(client, http):
    http.enqueue_data({"members": [], "total": 0})
    client.organization().members.list(page=2, page_size=50)
    assert http.last["params"] == {"page": 2, "pageSize": 50}


def test_invitations_create_uses_organization_role_id(client, http):
    http.enqueue_data(
        {"invitations": [{"id": 1, "email": "c@d.com", "status": "PENDING"}]}
    )
    invites = client.organization().invitations.create(
        ["c@d.com"], role_id="role_2"
    )
    assert invites[0].email == "c@d.com"
    assert http.last["json"] == {
        "emails": ["c@d.com"],
        "organizationRoleId": "role_2",
    }


def test_roles_create_sends_policy_ids(client, http):
    http.enqueue_data({"role": {"id": "r1", "name": "Analyst", "policies": []}})
    role = client.organization().roles.create(
        "Analyst", policy_ids=["p1"], description="read only"
    )
    assert role.name == "Analyst"
    assert http.last["json"] == {
        "name": "Analyst",
        "description": "read only",
        "policyIds": ["p1"],
    }


def test_policies_create_sends_permission_ids(client, http):
    http.enqueue_data(
        {"policy": {"id": "p1", "name": "Billing", "permissions": []}}
    )
    client.organization().policies.create("Billing", permission_ids=["perm1"])
    assert http.last["json"] == {
        "name": "Billing",
        "permissionIds": ["perm1"],
    }


def test_permissions_list(client, http):
    http.enqueue_data(
        {"permissions": [{"id": "perm1", "name": "billing:read"}]}
    )
    perms = client.organization().permissions.list()
    assert perms[0].name == "billing:read"
    assert http.last["url"].endswith("/v1/organization/permissions")
