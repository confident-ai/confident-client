import { ConfidentAI } from "../src";
import {
  API_BASE_URL,
  API_BASE_URL_EU,
} from "../src/api";
import { mockData, lastCall, resetAxios } from "./helpers";

jest.mock("axios");

describe("ConfidentAI", () => {
  const ORIGINAL_ENV = { ...process.env };

  beforeEach(() => {
    resetAxios();
    delete process.env.CONFIDENT_ORG_API_KEY;
    delete process.env.CONFIDENT_BASE_URL;
    delete process.env.CONFIDENT_REGION;
  });

  afterAll(() => {
    process.env = ORIGINAL_ENV;
  });

  it("initializes with an explicit API key", () => {
    const client = new ConfidentAI({ apiKey: "confident_us_org_abc" });
    expect(client.apiKey).toBe("confident_us_org_abc");
    expect(client.baseUrl).toBe(API_BASE_URL);
  });

  it("initializes from the environment variable", () => {
    process.env.CONFIDENT_ORG_API_KEY = "confident_us_org_env";
    const client = new ConfidentAI();
    expect(client.apiKey).toBe("confident_us_org_env");
  });

  it("throws when no API key is available", () => {
    expect(() => new ConfidentAI()).toThrow(/No Confident AI API key/);
  });

  it("honors an explicit base URL", () => {
    const client = new ConfidentAI({
      apiKey: "k",
      baseUrl: "https://example.test/api/",
    });
    expect(client.baseUrl).toBe("https://example.test/api");
  });

  it("selects the base URL from CONFIDENT_REGION", () => {
    process.env.CONFIDENT_REGION = "EU";
    const client = new ConfidentAI({ apiKey: "k" });
    expect(client.baseUrl).toBe(API_BASE_URL_EU);
  });

  it("infers the region from the API key prefix", () => {
    const client = new ConfidentAI({ apiKey: "confident_eu_org_xyz" });
    expect(client.baseUrl).toBe(API_BASE_URL_EU);
  });

  it("scopes a project client by id", () => {
    const client = new ConfidentAI({ apiKey: "k" });
    expect(client.project("proj_123").projectId).toBe("proj_123");
  });

  it("whoami returns the organization", async () => {
    const client = new ConfidentAI({ apiKey: "k" });
    mockData({ organization: { id: "org_1", name: "Acme" } });
    const org = await client.whoami();
    expect(org.id).toBe("org_1");
    expect(lastCall().method).toBe("GET");
    expect(lastCall().url).toContain("/v1/organization");
  });
});
