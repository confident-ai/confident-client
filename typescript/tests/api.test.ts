import { Api, Endpoints, HttpMethods } from "../src/api";
import { lastCall, mockData, mockRaw, mockedAxios, resetAxios } from "./helpers";

jest.mock("axios");

function makeApi(): Api {
  return new Api({ apiKey: "confident_us_org_k", baseUrl: "https://api.test" });
}

describe("Api", () => {
  beforeEach(() => resetAxios());

  it("sets auth and version headers", async () => {
    const api = makeApi();
    mockData({ ok: true });
    await api.sendRequest(HttpMethods.GET, Endpoints.ORGANIZATION_ENDPOINT);
    const headers = lastCall().headers;
    expect(headers.CONFIDENT_API_KEY).toBe("confident_us_org_k");
    expect(headers["Content-Type"]).toBe("application/json");
    expect(headers["X-Confident-SDK-Version"]).toContain("confidentai-ts/");
  });

  it("unwraps the data envelope on GET", async () => {
    const api = makeApi();
    mockData({ value: 42 });
    const result = await api.sendRequest<{ value: number }>(
      HttpMethods.GET,
      Endpoints.ORGANIZATION_ENDPOINT,
    );
    expect(result).toEqual({ value: 42 });
  });

  it("serializes a JSON body on PUT", async () => {
    const api = makeApi();
    mockData({});
    await api.sendRequest(HttpMethods.PUT, Endpoints.ORGANIZATION_ENDPOINT, {
      body: { name: "Acme" },
    });
    expect(lastCall().method).toBe("PUT");
    expect(lastCall().data).toEqual({ name: "Acme" });
  });

  it("drops undefined/null query params", async () => {
    const api = makeApi();
    mockData({});
    await api.sendRequest(
      HttpMethods.GET,
      Endpoints.ORGANIZATION_MEMBERS_ENDPOINT,
      { params: { page: 1, pageSize: undefined } },
    );
    expect(lastCall().params).toEqual({ page: 1 });
  });

  it("substitutes :param placeholders from urlParams", async () => {
    const api = makeApi();
    mockData({});
    await api.sendRequest(
      HttpMethods.DELETE,
      Endpoints.PROJECT_API_KEY_ENDPOINT,
      { urlParams: { projectId: "p1", apiKeyId: 42 } },
    );
    expect(lastCall().url).toContain("/v1/projects/p1/api-keys/42");
    expect(lastCall().url).not.toContain(":projectId");
    expect(lastCall().url).not.toContain(":apiKeyId");
  });

  it.each([400, 401, 403, 404, 422, 429, 500])(
    "throws on unsuccessful status %s",
    async (status) => {
      const api = makeApi();
      mockRaw({ success: false, error: "boom" }, status as number);
      await expect(
        api.sendRequest(HttpMethods.GET, Endpoints.ORGANIZATION_ENDPOINT),
      ).rejects.toThrow("boom");
    },
  );

  it("throws when success is false at status 200", async () => {
    const api = makeApi();
    mockRaw({ success: false, error: "nope" }, 200);
    await expect(
      api.sendRequest(HttpMethods.GET, Endpoints.ORGANIZATION_ENDPOINT),
    ).rejects.toThrow("nope");
  });

  it("surfaces network failures as errors", async () => {
    const api = makeApi();
    mockedAxios.mockRejectedValueOnce(new Error("ECONNRESET"));
    await expect(
      api.sendRequest(HttpMethods.GET, Endpoints.ORGANIZATION_ENDPOINT),
    ).rejects.toThrow("ECONNRESET");
  });
});
