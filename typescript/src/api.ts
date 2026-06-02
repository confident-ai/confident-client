import axios from "axios";

export const SDK_VERSION = "0.1.0";

// Organization-scoped API key env var. Named CONFIDENT_ORG_API_KEY (not
// CONFIDENT_API_KEY) to avoid clashing with deepeval's CONFIDENT_API_KEY, which
// holds a project key for a different SDK.
export const CONFIDENT_ORG_API_KEY_ENV_VAR = "CONFIDENT_ORG_API_KEY";
export const CONFIDENT_BASE_URL_ENV_VAR = "CONFIDENT_BASE_URL";
export const CONFIDENT_REGION_ENV_VAR = "CONFIDENT_REGION";

export const API_BASE_URL = "https://api.confident-ai.com";
export const API_BASE_URL_EU = "https://eu.api.confident-ai.com";

// Wire header the backend expects; unrelated to the env var name above.
export const API_KEY_HEADER = "CONFIDENT_API_KEY";
export const SDK_VERSION_HEADER = "X-Confident-SDK-Version";

export const DEFAULT_TIMEOUT_MS = 30000;

const RETRYABLE_ERROR_CODES = [
  "ECONNRESET",
  "ETIMEDOUT",
  "ECONNREFUSED",
  "ENOTFOUND",
  "ENETUNREACH",
  "ESOCKETTIMEDOUT",
  "CERT_HAS_EXPIRED",
];

function logRetryError(error: unknown, attempt: number): void {
  console.error(`Confident AI Error: ${error}. Retrying: ${attempt} time(s)...`);
}

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export enum HttpMethods {
  GET = "GET",
  POST = "POST",
  DELETE = "DELETE",
  PUT = "PUT",
}

export enum Endpoints {
  // Organization management
  ORGANIZATION_ENDPOINT = "/v1/organization",
  ORGANIZATION_MEMBERS_ENDPOINT = "/v1/organization/members",
  ORGANIZATION_MEMBER_ENDPOINT = "/v1/organization/members/:userId",
  ORGANIZATION_INVITATIONS_ENDPOINT = "/v1/organization/invitations",
  ORGANIZATION_INVITATION_ENDPOINT = "/v1/organization/invitations/:invitationId",
  ORGANIZATION_ROLES_ENDPOINT = "/v1/organization/roles",
  ORGANIZATION_ROLE_ENDPOINT = "/v1/organization/roles/:roleId",
  ORGANIZATION_POLICIES_ENDPOINT = "/v1/organization/policies",
  ORGANIZATION_POLICY_ENDPOINT = "/v1/organization/policies/:policyId",
  ORGANIZATION_PERMISSIONS_ENDPOINT = "/v1/organization/permissions",
  ORGANIZATION_API_KEYS_ENDPOINT = "/v1/organization/api-keys",
  ORGANIZATION_API_KEY_ENDPOINT = "/v1/organization/api-keys/:apiKeyId",

  // Project management
  PROJECTS_ENDPOINT = "/v1/projects",
  PROJECT_ENDPOINT = "/v1/projects/:projectId",
  PROJECT_MEMBERS_ENDPOINT = "/v1/projects/:projectId/members",
  PROJECT_MEMBER_ENDPOINT = "/v1/projects/:projectId/members/:userId",
  PROJECT_INVITATIONS_ENDPOINT = "/v1/projects/:projectId/invitations",
  PROJECT_INVITATION_ENDPOINT = "/v1/projects/:projectId/invitations/:invitationId",
  PROJECT_ROLES_ENDPOINT = "/v1/projects/:projectId/roles",
  PROJECT_ROLE_ENDPOINT = "/v1/projects/:projectId/roles/:roleId",
  PROJECT_POLICIES_ENDPOINT = "/v1/projects/:projectId/policies",
  PROJECT_POLICY_ENDPOINT = "/v1/projects/:projectId/policies/:policyId",
  PROJECT_PERMISSIONS_ENDPOINT = "/v1/projects/:projectId/permissions",
  PROJECT_API_KEYS_ENDPOINT = "/v1/projects/:projectId/api-keys",
  PROJECT_API_KEY_ENDPOINT = "/v1/projects/:projectId/api-keys/:apiKeyId",
}

export interface RequestOptions {
  body?: unknown;
  params?: Record<string, unknown>;
  urlParams?: Record<string, string | number>;
}

interface RetryOptions {
  maxAttempts: number;
  initialDelay: number;
  maxDelay: number;
  factor: number;
  jitter: boolean;
}

const defaultRetryOptions: RetryOptions = {
  maxAttempts: 5,
  initialDelay: 1000,
  maxDelay: 10000,
  factor: 2,
  jitter: true,
};

function inferRegionFromApiKey(apiKey?: string): string | undefined {
  if (!apiKey) return undefined;
  const key = apiKey.trim().toLowerCase();
  if (key.startsWith("confident_eu_")) return "EU";
  if (key.startsWith("confident_us_")) return "US";
  return undefined;
}

export function getConfidentApiKey(apiKey?: string): string | undefined {
  return apiKey || process.env[CONFIDENT_ORG_API_KEY_ENV_VAR] || undefined;
}

export function getBaseApiUrl(apiKey?: string, baseUrl?: string): string {
  if (baseUrl) {
    return baseUrl.replace(/\/+$/, "");
  }
  const fromEnv = process.env[CONFIDENT_BASE_URL_ENV_VAR];
  if (fromEnv) {
    return fromEnv.replace(/\/+$/, "");
  }
  const region = (
    process.env[CONFIDENT_REGION_ENV_VAR] ||
    inferRegionFromApiKey(apiKey) ||
    "US"
  ).toUpperCase();
  if (region === "EU") return API_BASE_URL_EU;
  return API_BASE_URL;
}

function dropUndefined(
  params?: Record<string, unknown>,
): Record<string, unknown> | undefined {
  if (!params) return undefined;
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      result[key] = value;
    }
  }
  return result;
}

export class Api {
  readonly apiKey: string;
  readonly baseUrl: string;
  readonly timeout: number;
  private readonly headers: Record<string, string>;

  constructor(options: {
    apiKey?: string;
    baseUrl?: string;
    timeout?: number;
  }) {
    const apiKey = getConfidentApiKey(options.apiKey);
    if (!apiKey) {
      throw new Error(
        `No Confident AI API key found. Pass { apiKey } or set the ${CONFIDENT_ORG_API_KEY_ENV_VAR} environment variable.`,
      );
    }

    this.apiKey = apiKey;
    this.baseUrl = getBaseApiUrl(apiKey, options.baseUrl);
    this.timeout = options.timeout ?? DEFAULT_TIMEOUT_MS;
    this.headers = {
      "Content-Type": "application/json",
      [API_KEY_HEADER]: apiKey,
      [SDK_VERSION_HEADER]: `confidentai-ts/${SDK_VERSION}`,
    };
  }

  private async httpRequest(
    method: string,
    url: string,
    data?: unknown,
    params?: Record<string, unknown>,
    options: RetryOptions = defaultRetryOptions,
  ): Promise<{ status: number; data: unknown }> {
    let attempt = 0;
    let delay = options.initialDelay;

    while (attempt < options.maxAttempts) {
      try {
        return await axios({
          method,
          url,
          headers: this.headers,
          data,
          params,
          timeout: this.timeout,
        });
      } catch (error: unknown) {
        attempt++;
        const code = (error as { code?: string }).code;
        const isRetryable =
          !!code && RETRYABLE_ERROR_CODES.some((c) => code.includes(c));

        if (!isRetryable || attempt >= options.maxAttempts) {
          throw error;
        }

        logRetryError(error, attempt);

        if (options.jitter) {
          const jitterFactor = Math.random() + 0.5;
          delay = Math.min(delay * options.factor * jitterFactor, options.maxDelay);
        } else {
          delay = Math.min(delay * options.factor, options.maxDelay);
        }

        await wait(delay);
      }
    }

    throw new Error(`Request failed after ${options.maxAttempts} attempts`);
  }

  async sendRequest<T = unknown>(
    method: HttpMethods,
    endpoint: Endpoints,
    options: RequestOptions = {},
  ): Promise<T> {
    let path: string = endpoint;
    if (options.urlParams) {
      for (const [key, value] of Object.entries(options.urlParams)) {
        path = path.replace(`:${key}`, String(value));
      }
    }
    const url = `${this.baseUrl}${path}`;

    try {
      const res = await this.httpRequest(
        method,
        url,
        options.body,
        dropUndefined(options.params),
      );
      return this.handleResponse<T>(res);
    } catch (error: unknown) {
      const err = error as {
        response?: { data?: { error?: string } };
        message?: string;
      };
      throw new Error(err.response?.data?.error || err.message || String(error));
    }
  }

  private handleResponse<T>(res: { status: number; data: unknown }): T {
    const { status, data: body } = res;

    if (status !== 200) {
      const message =
        (body as { error?: string })?.error ||
        `Request failed with status code ${status}`;
      throw new Error(message);
    }

    if (body && typeof body === "object") {
      const envelope = body as Record<string, unknown>;
      if (envelope.success === false) {
        throw new Error((envelope.error as string) || "Request failed");
      }
      if ("success" in envelope && "data" in envelope) {
        return envelope.data as T;
      }
    }
    return body as T;
  }
}
