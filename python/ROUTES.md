# Confident AI Python SDK — Route Map

This file maps the Confident AI **platform management API** to the methods this
SDK exposes. It is the human-readable counterpart to `tests/test_routes.py`,
which asserts each method calls the right HTTP method and path.

## Scope & source of truth

This SDK wraps the **management API** — organizations, projects, and their IAM
sub-resources (API keys, members, invitations, roles, policies, permissions).

* **Source:** `confident-docs/fern/openapi.yaml` (the published OpenAPI 3.1
  spec that drives the API reference at
  `https://www.confident-ai.com/docs/api-reference`).
* **Base URL:** `https://api.confident-ai.com` (region variant:
  `https://eu.api.confident-ai.com`).
* **Auth:** raw token in the `CONFIDENT_API_KEY` request header. These
  management endpoints require an **organization** API key.
* **Envelope:** responses are wrapped in `{ "success": true, "data": { ... } }`;
  the SDK returns the unwrapped `data`.

### Intentionally out of scope

The data-plane resources (datasets, traces, spans, test runs, evaluations,
prompts, metrics, annotations, threads) are **project-key-scoped** — the project
is implicit in the API key rather than addressed by a path parameter. They do
not fit a `client.project(project_id)`-scoped, organization-key client, and they
are already covered by the [`deepeval`](https://github.com/confident-ai/deepeval)
SDK. They are deliberately omitted here to avoid inventing routes that do not
exist (e.g. there is no `GET /v1/projects/{id}/datasets`).

Legend: **Implemented** = exposed by this SDK. Source = `Docs` (OpenAPI spec).

## Organization

| Resource | Method | Path | SDK Method | Implemented | Source |
| --- | --- | --- | --- | --- | --- |
| Organization | GET | `/v1/organization` | `client.organization().get()` | Yes | Docs |
| Organization | PUT | `/v1/organization` | `client.organization().update(name=...)` | Yes | Docs |
| Org API Keys | GET | `/v1/organization/api-keys` | `client.organization().api_keys.list()` | Yes | Docs |
| Org API Keys | POST | `/v1/organization/api-keys` | `client.organization().api_keys.create(name)` | Yes | Docs |
| Org API Keys | GET | `/v1/organization/api-keys/{apiKeyId}` | `client.organization().api_keys.get(api_key_id)` | Yes | Docs |
| Org API Keys | PUT | `/v1/organization/api-keys/{apiKeyId}` | `client.organization().api_keys.update(api_key_id, valid=...)` | Yes | Docs |
| Org API Keys | DELETE | `/v1/organization/api-keys/{apiKeyId}` | `client.organization().api_keys.delete(api_key_id)` | Yes | Docs |
| Org Members | GET | `/v1/organization/members` | `client.organization().members.list(page=, page_size=)` | Yes | Docs |
| Org Members | PUT | `/v1/organization/members/{userId}` | `client.organization().members.update_role(user_id, role_id=...)` | Yes | Docs |
| Org Members | DELETE | `/v1/organization/members/{userId}` | `client.organization().members.remove(user_id)` | Yes | Docs |
| Org Invitations | GET | `/v1/organization/invitations` | `client.organization().invitations.list()` | Yes | Docs |
| Org Invitations | POST | `/v1/organization/invitations` | `client.organization().invitations.create(emails, role_id=...)` | Yes | Docs |
| Org Invitations | PUT | `/v1/organization/invitations/{invitationId}` | `client.organization().invitations.resend(invitation_id)` | Yes | Docs |
| Org Invitations | DELETE | `/v1/organization/invitations/{invitationId}` | `client.organization().invitations.revoke(invitation_id)` | Yes | Docs |
| Org Roles | GET | `/v1/organization/roles` | `client.organization().roles.list()` | Yes | Docs |
| Org Roles | POST | `/v1/organization/roles` | `client.organization().roles.create(name, policy_ids=...)` | Yes | Docs |
| Org Roles | PUT | `/v1/organization/roles/{roleId}` | `client.organization().roles.update(role_id, name=, policy_ids=)` | Yes | Docs |
| Org Roles | DELETE | `/v1/organization/roles/{roleId}` | `client.organization().roles.delete(role_id)` | Yes | Docs |
| Org Policies | GET | `/v1/organization/policies` | `client.organization().policies.list()` | Yes | Docs |
| Org Policies | POST | `/v1/organization/policies` | `client.organization().policies.create(name, permission_ids=...)` | Yes | Docs |
| Org Policies | PUT | `/v1/organization/policies/{policyId}` | `client.organization().policies.update(policy_id, name=, permission_ids=)` | Yes | Docs |
| Org Policies | DELETE | `/v1/organization/policies/{policyId}` | `client.organization().policies.delete(policy_id)` | Yes | Docs |
| Org Permissions | GET | `/v1/organization/permissions` | `client.organization().permissions.list()` | Yes | Docs |

## Projects

| Resource | Method | Path | SDK Method | Implemented | Source |
| --- | --- | --- | --- | --- | --- |
| Projects | GET | `/v1/projects` | `client.projects.list()` | Yes | Docs |
| Projects | POST | `/v1/projects` | `client.projects.create(name, description=, email=)` | Yes | Docs |
| Projects | GET | `/v1/projects/{projectId}` | `client.project(id).get()` | Yes | Docs |
| Projects | PUT | `/v1/projects/{projectId}` | `client.project(id).update(...)` | Yes | Docs |
| Projects | DELETE | `/v1/projects/{projectId}` | `client.project(id).delete()` | Yes | Docs |
| Project API Keys | GET | `/v1/projects/{projectId}/api-keys` | `client.project(id).api_keys.list()` | Yes | Docs |
| Project API Keys | POST | `/v1/projects/{projectId}/api-keys` | `client.project(id).api_keys.create(name)` | Yes | Docs |
| Project API Keys | GET | `/v1/projects/{projectId}/api-keys/{apiKeyId}` | `client.project(id).api_keys.get(api_key_id)` | Yes | Docs |
| Project API Keys | PUT | `/v1/projects/{projectId}/api-keys/{apiKeyId}` | `client.project(id).api_keys.update(api_key_id, valid=...)` | Yes | Docs |
| Project API Keys | DELETE | `/v1/projects/{projectId}/api-keys/{apiKeyId}` | `client.project(id).api_keys.delete(api_key_id)` | Yes | Docs |
| Project Members | GET | `/v1/projects/{projectId}/members` | `client.project(id).members.list(page=, page_size=)` | Yes | Docs |
| Project Members | PUT | `/v1/projects/{projectId}/members/{userId}` | `client.project(id).members.update_role(user_id, role_id=...)` | Yes | Docs |
| Project Members | DELETE | `/v1/projects/{projectId}/members/{userId}` | `client.project(id).members.remove(user_id)` | Yes | Docs |
| Project Invitations | GET | `/v1/projects/{projectId}/invitations` | `client.project(id).invitations.list()` | Yes | Docs |
| Project Invitations | POST | `/v1/projects/{projectId}/invitations` | `client.project(id).invitations.create(emails, role_id=...)` | Yes | Docs |
| Project Invitations | PUT | `/v1/projects/{projectId}/invitations/{invitationId}` | `client.project(id).invitations.resend(invitation_id)` | Yes | Docs |
| Project Invitations | DELETE | `/v1/projects/{projectId}/invitations/{invitationId}` | `client.project(id).invitations.revoke(invitation_id)` | Yes | Docs |
| Project Roles | GET | `/v1/projects/{projectId}/roles` | `client.project(id).roles.list()` | Yes | Docs |
| Project Roles | POST | `/v1/projects/{projectId}/roles` | `client.project(id).roles.create(name, policy_ids=...)` | Yes | Docs |
| Project Roles | PUT | `/v1/projects/{projectId}/roles/{roleId}` | `client.project(id).roles.update(role_id, name=, policy_ids=)` | Yes | Docs |
| Project Roles | DELETE | `/v1/projects/{projectId}/roles/{roleId}` | `client.project(id).roles.delete(role_id)` | Yes | Docs |
| Project Policies | GET | `/v1/projects/{projectId}/policies` | `client.project(id).policies.list()` | Yes | Docs |
| Project Policies | POST | `/v1/projects/{projectId}/policies` | `client.project(id).policies.create(name, permission_ids=...)` | Yes | Docs |
| Project Policies | PUT | `/v1/projects/{projectId}/policies/{policyId}` | `client.project(id).policies.update(policy_id, name=, permission_ids=)` | Yes | Docs |
| Project Policies | DELETE | `/v1/projects/{projectId}/policies/{policyId}` | `client.project(id).policies.delete(policy_id)` | Yes | Docs |
| Project Permissions | GET | `/v1/projects/{projectId}/permissions` | `client.project(id).permissions.list()` | Yes | Docs |

## Notes

* `client.projects.create(...)` returns the new project **and** a freshly minted
  project API key whose full `value` is only ever returned once.
* `members.invite(...)` is intentionally **not** a method — inviting members is
  done via the invitations resource (`invitations.create(emails, role_id=...)`),
  matching the real API.
* Role/policy `update` requires `name` and `policy_ids`/`permission_ids` because
  the API uses the same `CreateOrUpdate*` schema for create and update.
