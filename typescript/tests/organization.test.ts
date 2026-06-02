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
      .roles.create({ name: "Analyst", policyIds: ["p1"] });
    expect(lastCall().data).toEqual({
      name: "Analyst",
      description: undefined,
      policyIds: ["p1"],
    });
  });

  it("lists permissions", async () => {
    mockData({ permissions: [{ id: "perm1", name: "billing:read" }] });
    const perms = await makeClient().organization().permissions.list();
    expect(perms[0].name).toBe("billing:read");
    expect(lastCall().url).toContain("/v1/organization/permissions");
  });
});
