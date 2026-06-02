import { ConfidentAI } from "../src";
import { lastCall, mockData, resetAxios } from "./helpers";

jest.mock("axios");

function makeClient(): ConfidentAI {
  return new ConfidentAI({ apiKey: "confident_us_org_k" });
}

describe("Projects", () => {
  beforeEach(() => resetAxios());

  it("lists projects", async () => {
    mockData({ projects: [{ id: "p1", name: "Prod", organizationId: "o1" }] });
    const projects = await makeClient().projects.list();
    expect(projects[0].id).toBe("p1");
    expect(projects[0].organizationId).toBe("o1");
    expect(lastCall().url).toContain("/v1/projects");
  });

  it("creates a project and returns its API key", async () => {
    mockData({
      project: { id: "p1", name: "New" },
      apiKey: { id: 7, valid: true, value: "confident_proj_secret" },
    });
    const created = await makeClient().projects.create({
      name: "New",
      description: "desc",
    });
    expect(created.project.id).toBe("p1");
    expect(created.apiKey?.value).toBe("confident_proj_secret");
    expect(lastCall().data).toEqual({
      name: "New",
      description: "desc",
      email: undefined,
    });
  });

  it("scopes a project by id", () => {
    expect(makeClient().project("proj_123").projectId).toBe("proj_123");
  });

  it("gets a scoped project", async () => {
    mockData({ project: { id: "proj_123", name: "Prod" } });
    const project = await makeClient().project("proj_123").get();
    expect(project.id).toBe("proj_123");
    expect(lastCall().url).toContain("/v1/projects/proj_123");
  });

  it("deletes a scoped project", async () => {
    mockData({ id: "proj_123", deleted: true });
    const result = await makeClient().project("proj_123").delete();
    expect(result.deleted).toBe(true);
    expect(lastCall().method).toBe("DELETE");
    expect(lastCall().url).toContain("/v1/projects/proj_123");
  });

  it("uses scoped paths for project API keys", async () => {
    mockData({ apiKeys: [] });
    await makeClient().project("proj_123").apiKeys.list();
    expect(lastCall().url).toContain("/v1/projects/proj_123/api-keys");
  });

  it("creates project invitations with projectRoleId", async () => {
    mockData({ invitations: [] });
    await makeClient()
      .project("proj_123")
      .invitations.create({ emails: ["e@f.com"], roleId: "prole_1" });
    expect(lastCall().data).toEqual({
      emails: ["e@f.com"],
      projectRoleId: "prole_1",
    });
    expect(lastCall().url).toContain("/v1/projects/proj_123/invitations");
  });
});
