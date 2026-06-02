import { Api, Endpoints, HttpMethods } from "../../api";
import { ApiKey, DeletionResult } from "../../types";
import {
  ApiKeyHttpResponse,
  ApiKeysHttpResponse,
  CreateApiKeyRequest,
  UpdateApiKeyRequest,
} from "./types";

export class ProjectApiKeys {
  constructor(
    private readonly api: Api,
    private readonly projectId: string,
  ) {}

  async list(): Promise<ApiKey[]> {
    const data = await this.api.sendRequest<ApiKeysHttpResponse>(
      HttpMethods.GET,
      Endpoints.PROJECT_API_KEYS_ENDPOINT,
      { urlParams: { projectId: this.projectId } },
    );
    return data.apiKeys ?? [];
  }

  async get(apiKeyId: number): Promise<ApiKey> {
    const data = await this.api.sendRequest<ApiKeyHttpResponse>(
      HttpMethods.GET,
      Endpoints.PROJECT_API_KEY_ENDPOINT,
      { urlParams: { projectId: this.projectId, apiKeyId } },
    );
    return data.apiKey;
  }

  async create(params: CreateApiKeyRequest): Promise<ApiKey> {
    const body: CreateApiKeyRequest = { name: params.name };
    const data = await this.api.sendRequest<ApiKeyHttpResponse>(
      HttpMethods.POST,
      Endpoints.PROJECT_API_KEYS_ENDPOINT,
      { body, urlParams: { projectId: this.projectId } },
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
      Endpoints.PROJECT_API_KEY_ENDPOINT,
      { body, urlParams: { projectId: this.projectId, apiKeyId } },
    );
    return data.apiKey;
  }

  async delete(apiKeyId: number): Promise<DeletionResult> {
    return this.api.sendRequest<DeletionResult>(
      HttpMethods.DELETE,
      Endpoints.PROJECT_API_KEY_ENDPOINT,
      { urlParams: { projectId: this.projectId, apiKeyId } },
    );
  }
}
