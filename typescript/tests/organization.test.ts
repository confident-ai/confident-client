import { ConfidentAI } from "../src";
import { lastCall, mockData, resetAxios } from "./helpers";

jest.mock("axios");

function makeClient(): ConfidentAI {
  return new ConfidentAI({ apiKey: "confident_us_org_k" });
}

describe("OrganizationClient", () => {
  beforeEach(() => resetAxios());

  it("gets the organization", async () => {
    mockData({ organization: { id: "org_1", name: "Acme", plan: "PREMIUM" } });
    const org = await makeClient().organization().get();
    expect(org.id).toBe("org_1");
    expect(lastCall().method).toBe("GET");
    expect(lastCall().url).toContain("/v1/organization");
  });

  it("updates the organization", async () => {
    mockData({ organization: { id: "org_1", name: "New" } });
    const org = await makeClient().organization().update({ name: "New" });
    expect(org.name).toBe("New");
    expect(lastCall().method).toBe("PUT");
    expect(lastCall().data).toEqual({ name: "New" });
  });

  it("creates an API key", async () => {
    mockData({
      apiKey: { id: 2, name: "CI", valid: true, value: "secret" },
    });
    const key = await makeClient().organization().apiKeys.create({ name: "CI" });
    expect(key.value).toBe("secret");
    expect(lastCall().method).toBe("POST");
    expect(lastCall().url).toContain("/v1/organization/api-keys");
    expect(lastCall().data).toEqual({ name: "CI" });
  });

  it("updates a member role", async () => {
    mockData({
      member: {
        id: "u1",
        email: "a@b.com",
        organizationRole: { id: "r1", name: "Admin" },
      },
    });
    const member = await makeClient()
      .organization()
      .members.updateRole("u1", { roleId: "r1" });
    expect(member.organizationRole?.name).toBe("Admin");
    expect(lastCall().data).toEqual({ roleId: "r1" });
    expect(lastCall().url).toContain("/v1/organization/members/u1");
  });

  it("creates invitations with organizationRoleId", async () => {
    mockData({ invitations: [{ id: 1, email: "c@d.com", status: "PENDING" }] });
    await makeClient()
      .organization()
      .invitations.create({ emails: ["c@d.com"], roleId: "r2" });
    expect(lastCall().data).toEqual({
      emails: ["c@d.com"],
      organizationRoleId: "r2",
    });
  });

  it("creates a role with policyIds", async () => {
    mockData({ role: { id: "r1", name: "Analyst", policies: [] } });
    await makeClient()
      .organization()
      .iam.roles.create({ name: "Analyst", policyIds: ["p1"] });
    expect(lastCall().data).toEqual({
      name: "Analyst",
      description: undefined,
      policyIds: ["p1"],
    });
  });

  it("lists permissions", async () => {
    mockData({ permissions: [{ id: "perm1", name: "billing:read" }] });
    const perms = await makeClient().organization().iam.permissions.list();
    expect(perms[0].name).toBe("billing:read");
    expect(lastCall().url).toContain("/v1/organization/permissions");
  });

  it("lists governance policies with projectsCount and controls", async () => {
    mockData({
      governancePolicies: [
        {
          id: "gp1",
          name: "Production Gate",
          projectsCount: 5,
          controls: [
            { id: "c1", name: "Logs traces", type: "PRE_DEPLOYMENT_EVALS" },
          ],
        },
      ],
    });
    const policies = await makeClient()
      .organization()
      .governance.policies.list();
    expect(policies[0].id).toBe("gp1");
    expect(policies[0].projectsCount).toBe(5);
    expect(policies[0].controls[0].type).toBe("PRE_DEPLOYMENT_EVALS");
    expect(lastCall().url).toContain("/v1/organization/governance-policies");
  });

  it("lists a governance policy's projects (paginated)", async () => {
    mockData({ projects: [{ id: "p1", name: "Prod" }], total: 1 });
    const projects = await makeClient()
      .organization()
      .governance.policies.listProjects("gp1", { page: 2, pageSize: 50 });
    expect(projects[0].id).toBe("p1");
    expect(lastCall().params).toEqual({ page: 2, pageSize: 50 });
    expect(lastCall().url).toContain(
      "/v1/organization/governance-policies/gp1/projects",
    );
  });

  it("assigns projects to a governance policy", async () => {
    mockData({
      governancePolicy: { id: "gp1", name: "Production Gate" },
      assignedProjectIds: ["p1", "p2"],
      notFoundProjectIds: [],
      count: 2,
    });
    const result = await makeClient()
      .organization()
      .governance.policies.assign("gp1", { projectIds: ["p1", "p2"] });
    expect(result.assignedProjectIds).toEqual(["p1", "p2"]);
    expect(result.notFoundProjectIds).toEqual([]);
    expect(result.count).toBe(2);
    expect(result.governancePolicy.id).toBe("gp1");
    expect(lastCall().method).toBe("POST");
    expect(lastCall().data).toEqual({ projectIds: ["p1", "p2"] });
    expect(lastCall().url).toContain(
      "/v1/organization/governance-policies/gp1/assign",
    );
  });

  it("unassigns projects from a governance policy", async () => {
    mockData({
      governancePolicy: { id: "gp1", name: "Production Gate" },
      unassignedProjectIds: ["p1"],
      skippedProjectIds: [],
      count: 1,
    });
    const result = await makeClient()
      .organization()
      .governance.policies.unassign("gp1", { projectIds: ["p1"] });
    expect(result.unassignedProjectIds).toEqual(["p1"]);
    expect(result.skippedProjectIds).toEqual([]);
    expect(result.count).toBe(1);
    expect(lastCall().method).toBe("POST");
    expect(lastCall().data).toEqual({ projectIds: ["p1"] });
    expect(lastCall().url).toContain(
      "/v1/organization/governance-policies/gp1/unassign",
    );
  });
});
