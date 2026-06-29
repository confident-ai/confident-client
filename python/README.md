# confidentai (Python)

The official Python SDK for the [Confident AI](https://www.confident-ai.com)
platform **management API** — manage organizations, projects, API keys, members,
invitations, roles, and policies.

> Looking to run evaluations, upload traces, or pull datasets? Use
> [`deepeval`](https://github.com/confident-ai/deepeval). This SDK focuses on
> platform/administration APIs.

## Installation

```bash
pip install confidentai
```

## Quickstart

```python
from confidentai import ConfidentAI

client = ConfidentAI(api_key="confident_org_...")

# The organization the API key is scoped to
organization = client.organization().get()

# All projects in the organization
projects = client.projects.list()

# A scoped project client
project = client.project("project_id")
members = project.members.list()
```

## Authentication

These endpoints require an **organization** API key. Provide it explicitly or
via the environment:

```python
client = ConfidentAI(api_key="confident_org_...")
```

```bash
export CONFIDENT_ORG_API_KEY="confident_org_..."
```

> Use `CONFIDENT_ORG_API_KEY`, **not** `CONFIDENT_API_KEY`. The latter is
> reserved by [`deepeval`](https://github.com/confident-ai/deepeval) for a
> project key; the distinct name lets both SDKs run side by side.

```python
from confidentai import ConfidentAI

client = ConfidentAI()  # reads CONFIDENT_ORG_API_KEY
```

### Configuration

`ConfidentAI(api_key=None, base_url=None, timeout=None)`

| Setting | Resolution order |
| --- | --- |
| `api_key` | `api_key` argument → `CONFIDENT_ORG_API_KEY` |
| `base_url` | `base_url` argument → `CONFIDENT_BASE_URL` → regional default |
| region | `CONFIDENT_REGION` (`US` / `EU`) → API key prefix → `US` |

Regional defaults: `https://api.confident-ai.com` (US),
`https://eu.api.confident-ai.com` (EU).

## Async

Every method that hits the API has an `a_`-prefixed async counterpart on the
same client (`list` / `a_list`, `assign` / `a_assign`, …) — the same style as
`deepeval`'s `measure` / `a_measure`. There is no separate async client; use one
`ConfidentAI` and `await` the `a_` methods in `asyncio` code:

```python
import asyncio

from confidentai import ConfidentAI


async def main():
    client = ConfidentAI(api_key="confident_org_...")

    organization = await client.a_whoami()
    projects = await client.projects.a_list()

    project = client.project("project_id")          # no I/O, no await
    members = await project.members.a_list()          # awaited

    created = await client.projects.a_create("Async App")
    await client.project(created.project.id).a_delete()


asyncio.run(main())
```

`organization()` and `project(id)` just build scoped clients (no network), so
they are not awaited; only the `a_`-prefixed methods that actually hit the API
are coroutines. Configuration, regions, and `ConfidentApiError` behave
identically to the sync methods.

## Organization example

```python
org_client = client.organization()

# Profile
organization = org_client.get()
org_client.update(name="Acme Inc.")

# API keys (the full value is returned only on create)
created = org_client.api_keys.create(name="CI/CD key")
print(created.value)
org_client.api_keys.update(created.id, valid=False)
org_client.api_keys.delete(created.id)

# Members & invitations
members = org_client.members.list(page=1, page_size=25)
org_client.members.update_role(members[0].id, role_id="role_id")
org_client.invitations.create(["teammate@acme.com"], role_id="role_id")

# IAM: roles, policies & permissions
permissions = org_client.iam.permissions.list()
policy = org_client.iam.policies.create(
    "Billing", permission_ids=[permissions[0].id]
)
org_client.iam.roles.create("Billing Manager", policy_ids=[policy.id])

# Governance: list policies and assign projects to one (great for CI/CD)
governance_policies = org_client.governance.policies.list()
if governance_policies:
    org_client.governance.policies.assign(
        governance_policies[0].id, project_ids=["project_id"]
    )
```

## Project example

```python
# Create a project (returns the project + its first API key)
created = client.projects.create("Production App", description="Main app")
print(created.project.id, created.api_key.value)

# List / fetch
projects = client.projects.list()
project = client.project(created.project.id)
project.update(name="Production")

# Project-scoped resources
project.api_keys.create(name="Production agent key")
project.members.list()
project.invitations.create(["analyst@acme.com"], role_id="project_role_id")

# Project-scoped IAM (roles, policies, permissions)
project.iam.roles.list()
project.iam.policies.list()
project.iam.permissions.list()

# Delete
project.delete()
```

## Error handling

When the API returns an unsuccessful response, the SDK raises
`ConfidentApiError`, which carries the error message and an optional `link` to
relevant docs.

```python
from confidentai import ConfidentAI, ConfidentApiError

client = ConfidentAI()

try:
    client.project("does-not-exist").get()
except ConfidentApiError as err:
    print("Something went wrong:", err, err.link)
```

## Development

```bash
cd python
poetry install
poetry run pytest
```

Or without Poetry:

```bash
cd python
python -m venv .venv && source .venv/bin/activate
pip install requests "pydantic>=2.11" tenacity aiohttp pytest
pytest
```

The default suite mocks the HTTP layer and never hits a real API, so it runs
anywhere (and is the pre-merge CI gate).

### Integration tests (optional, real API)

A separate, opt-in suite under `tests/integration/` exercises the live API. It
is **excluded** from the default run and auto-skips unless
`CONFIDENT_ORG_API_KEY` is set:

```bash
CONFIDENT_ORG_API_KEY="confident_org_..." poetry run pytest -m integration
```

Most checks are read-only (`whoami`, `projects.list`, `permissions.list`); the
project round-trip creates and then deletes a throwaway project. CI runs this
suite nightly / on demand via the `Integration` workflow, never on pull
requests.

See [`ROUTES.md`](./ROUTES.md) for the full endpoint → method map.
