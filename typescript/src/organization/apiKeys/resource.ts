import { Api, Endpoints, HttpMethods } from "../../api";
import { ApiKey, DeletionResult } from "../../types";
import {
  ApiKeyHttpResponse,
  ApiKeysHttpResponse,
  CreateApiKeyRequest,
  UpdateApiKeyRequest,
} from "./types";

export class OrganizationApiKeys {
  constructor(private readonly api: Api) {}

  async list(): Promise<ApiKey[]> {
    const data = await this.api.sendRequest<ApiKeysHttpResponse>(
      HttpMethods.GET,
      Endpoints.ORGANIZATION_API_KEYS_ENDPOINT,
    );
    return data.apiKeys ?? [];
  }

  async get(apiKeyId: number): Promise<ApiKey> {
    const data = await this.api.sendRequest<ApiKeyHttpResponse>(
      HttpMethods.GET,
      Endpoints.ORGANIZATION_API_KEY_ENDPOINT,
      { urlParams: { apiKeyId } },
    );
    return data.apiKey;
  }

  async create(params: CreateApiKeyRequest): Promise<ApiKey> {
    const body: CreateApiKeyRequest = { name: params.name };
    const data = await this.api.sendRequest<ApiKeyHttpResponse>(
      HttpMethods.POST,
      Endpoints.ORGANIZATION_API_KEYS_ENDPOINT,
      { body },
    );
    return data.apiKey;
  }

  async update(
    apiKeyId: number,
    params: UpdateApiKeyRequest,
  ): Promise<ApiKey> {
    const body: UpdateApiKeyRequest = { valid: params.valid };
    const data = await this.api.sendRequest<ApiKeyHttpResponse>(
      HttpMethods.PUT,
      Endpoints.ORGANIZATION_API_KEY_ENDPOINT,
      { body, urlParams: { apiKeyId } },
    );
    return data.apiKey;
  }

  async delete(apiKeyId: number): Promise<DeletionResult> {
    return this.api.sendRequest<DeletionResult>(
      HttpMethods.DELETE,
      Endpoints.ORGANIZATION_API_KEY_ENDPOINT,
      { urlParams: { apiKeyId } },
    );
  }
}
