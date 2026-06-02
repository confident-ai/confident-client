"""Verify SDK methods call the correct HTTP method and path.

This is the executable counterpart to ``ROUTES.md`` — it guards against
accidentally pointing a method at the wrong endpoint.
"""

import pytest


def call(client, spec):
    return spec(client)


# (description, callable, expected_method, expected_path_suffix)
ROUTE_CASES = [
    (
        "get organization",
        lambda c: c.organization().get(),
        "GET",
        "/v1/organization",
    ),
    (
        "update organization",
        lambda c: c.organization().update(name="x"),
        "PUT",
        "/v1/organization",
    ),
    (
        "list org members",
        lambda c: c.organization().members.list(),
        "GET",
        "/v1/organization/members",
    ),
    (
        "list org roles",
        lambda c: c.organization().roles.list(),
        "GET",
        "/v1/organization/roles",
    ),
    (
        "list org policies",
        lambda c: c.organization().policies.list(),
        "GET",
        "/v1/organization/policies",
    ),
    (
        "list org permissions",
        lambda c: c.organization().permissions.list(),
        "GET",
        "/v1/organization/permissions",
    ),
    (
        "list org invitations",
        lambda c: c.organization().invitations.list(),
        "GET",
        "/v1/organization/invitations",
    ),
    (
        "list org api keys",
        lambda c: c.organization().api_keys.list(),
        "GET",
        "/v1/organization/api-keys",
    ),
    (
        "list projects",
        lambda c: c.projects.list(),
        "GET",
        "/v1/projects",
    ),
    (
        "get project",
        lambda c: c.project("p1").get(),
        "GET",
        "/v1/projects/p1",
    ),
    (
        "delete project",
        lambda c: c.project("p1").delete(),
        "DELETE",
        "/v1/projects/p1",
    ),
    (
        "list project members",
        lambda c: c.project("p1").members.list(),
        "GET",
        "/v1/projects/p1/members",
    ),
    (
        "list project roles",
        lambda c: c.project("p1").roles.list(),
        "GET",
        "/v1/projects/p1/roles",
    ),
    (
        "list project permissions",
        lambda c: c.project("p1").permissions.list(),
        "GET",
        "/v1/projects/p1/permissions",
    ),
    (
        "list project api keys",
        lambda c: c.project("p1").api_keys.list(),
        "GET",
        "/v1/projects/p1/api-keys",
    ),
]


@pytest.mark.parametrize(
    "description,fn,method,path",
    ROUTE_CASES,
    ids=[c[0] for c in ROUTE_CASES],
)
def test_routes(client, http, description, fn, method, path):
    # Provide a permissive envelope so list/get parsing never blows up.
    http.enqueue_data(
        {
            "organization": {"id": "o", "name": "n"},
            "project": {"id": "p1", "name": "n"},
            "members": [],
            "roles": [],
            "policies": [],
            "permissions": [],
            "invitations": [],
            "apiKeys": [],
            "id": "p1",
            "deleted": True,
        }
    )
    fn(client)
    assert http.last["method"] == method
    assert http.last["url"].endswith(path)
