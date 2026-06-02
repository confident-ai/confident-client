# Confident AI SDKs

Official SDKs for the [Confident AI](https://www.confident-ai.com) platform
**management API** — programmatically manage organizations, projects, API keys,
members, invitations, roles, and policies.

| Language | Package | Location |
| --- | --- | --- |
| Python | `confidentai` | [`python/`](./python) |
| TypeScript | `confidentai` | [`typescript/`](./typescript) |

> **Evaluations, traces, datasets, prompts?** Those are project-key-scoped and
> live in [`deepeval`](https://github.com/confident-ai/deepeval) (Python) and
> [`deepeval`](https://www.npmjs.com/package/deepeval) (TypeScript). These SDKs
> focus on platform administration.

## Design

Both SDKs share one ergonomic surface:

```python
# Python
from confidentai import ConfidentAI

client = ConfidentAI(api_key="confident_org_...")
organization = client.organization().get()    # -> Organization
project = client.project("project_id").get()   # -> Project
projects = client.projects.list()              # -> list[Project]
```

```ts
// TypeScript
import { ConfidentAI } from "confidentai";

const client = new ConfidentAI({ apiKey: "confident_org_..." });
const organization = await client.organization().get();   // -> Organization
const project = await client.project("project_id").get();  // -> Project
const projects = await client.projects.list();             // -> Project[]
```

Scoped clients expose resources with consistent `list` / `get` / `create` /
`update` / `delete` methods (plus action methods like `invitations.create`,
`apiKeys.create`, `members.updateRole`):

```python
client.organization().members.list()
client.organization().roles.create("Analyst", policy_ids=[...])
client.project("id").api_keys.create(name="agent key")
```

## Authentication

These endpoints require an **organization** API key, supplied via the
`api_key`/`apiKey` argument or the `CONFIDENT_ORG_API_KEY` environment variable.
(It is intentionally **not** `CONFIDENT_API_KEY`, which `deepeval` already uses
for a project key — the distinct name lets both SDKs coexist.) The base URL
resolves from `CONFIDENT_BASE_URL` or `CONFIDENT_REGION` (`US` / `EU`),
defaulting to `https://api.confident-ai.com`.

## Conventions

* **Python** mirrors [`deepeval`](https://github.com/confident-ai/deepeval):
  Poetry, `requests`, Pydantic v2, the `CONFIDENT_API_KEY` header, the
  `{ success, data }` response envelope, and pytest.
* **TypeScript** mirrors `deepeval.ts`: `tsc` build, `axios`, interface-based
  types, and Jest with `jest.mock("axios")`.

## Development

```bash
# Python
cd python && poetry install && poetry run pytest

# TypeScript
cd typescript && npm install && npm test && npm run build
```

See [`python/ROUTES.md`](./python/ROUTES.md) for the full endpoint → method map.
