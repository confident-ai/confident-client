# confidentai (TypeScript)

The official TypeScript SDK for the [Confident AI](https://www.confident-ai.com)
platform **management API** — manage organizations, projects, API keys, members,
invitations, roles, and policies.

> Looking to run evaluations, upload traces, or pull datasets? Use
> [`deepeval`](https://www.npmjs.com/package/deepeval). This SDK focuses on
> platform/administration APIs.

## Installation

```bash
npm install confidentai
```

## Quickstart

```ts
import { ConfidentAI } from "confidentai";

const client = new ConfidentAI({ apiKey: "confident_org_..." });

// The organization the API key is scoped to
const organization = await client.organization().get();

// All projects in the organization
const projects = await client.projects.list();

// A scoped project client
const project = client.project("project_id");
const members = await project.members.list();
```

## Authentication

These endpoints require an **organization** API key. Provide it explicitly or
via the `CONFIDENT_ORG_API_KEY` environment variable:

```ts
const client = new ConfidentAI({ apiKey: "confident_org_..." });
// or
const client = new ConfidentAI(); // reads process.env.CONFIDENT_ORG_API_KEY
```

> Use `CONFIDENT_ORG_API_KEY`, **not** `CONFIDENT_API_KEY`. The latter is
> reserved by [`deepeval`](https://www.npmjs.com/package/deepeval) for a project
> key; the distinct name lets both SDKs run side by side.

### Configuration

`new ConfidentAI({ apiKey?, baseUrl?, timeout? })`

| Setting | Resolution order |
| --- | --- |
| `apiKey` | `apiKey` option → `CONFIDENT_ORG_API_KEY` |
| `baseUrl` | `baseUrl` option → `CONFIDENT_BASE_URL` → regional default |
| region | `CONFIDENT_REGION` (`US` / `EU`) → API key prefix → `US` |
| `timeout` | milliseconds (default `30000`) |

Regional defaults: `https://api.confident-ai.com` (US),
`https://eu.api.confident-ai.com` (EU).

## Organization example

```ts
const org = client.organization();

await org.get();
await org.update({ name: "Acme Inc." });

// API keys (the full value is returned only on create)
const created = await org.apiKeys.create({ name: "CI/CD key" });
console.log(created.value);
await org.apiKeys.update(created.id, { valid: false });
await org.apiKeys.delete(created.id);

// Members & invitations
const members = await org.members.list({ page: 1, pageSize: 25 });
await org.members.updateRole(members[0].id, { roleId: "role_id" });
await org.invitations.create({ emails: ["teammate@acme.com"], roleId: "role_id" });

// IAM: roles, policies & permissions
const permissions = await org.iam.permissions.list();
const policy = await org.iam.policies.create({
  name: "Billing",
  permissionIds: [permissions[0].id],
});
await org.iam.roles.create({ name: "Billing Manager", policyIds: [policy.id] });

// Governance: list policies and assign projects to one (great for CI/CD)
const governancePolicies = await org.governance.policies.list();
if (governancePolicies.length > 0) {
  await org.governance.policies.assign(governancePolicies[0].id, {
    projectIds: ["project_id"],
  });
}
```

## Project example

```ts
// Create a project (returns the project + its first API key)
const created = await client.projects.create({ name: "Production App" });
console.log(created.project.id, created.apiKey?.value);

// List / fetch
const projects = await client.projects.list();
const project = client.project(created.project.id);
await project.update({ name: "Production" });

// Project-scoped resources
await project.apiKeys.create({ name: "Production agent key" });
await project.members.list();
await project.invitations.create({
  emails: ["analyst@acme.com"],
  roleId: "project_role_id",
});

// Project-scoped IAM (roles, policies, permissions)
await project.iam.roles.list();
await project.iam.policies.list();
await project.iam.permissions.list();

// Delete
await project.delete();
```

## Error handling

When the API returns an unsuccessful response, `sendRequest` throws an `Error`
whose message is the server-provided error (or the HTTP status text).

```ts
import { ConfidentAI } from "confidentai";

const client = new ConfidentAI();

try {
  await client.project("does-not-exist").get();
} catch (err) {
  console.log("Something went wrong:", (err as Error).message);
}
```

## Development

```bash
cd typescript
npm install
npm test
npm run build
```

Tests mock `axios` and never hit a real API.
