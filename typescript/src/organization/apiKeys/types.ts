import { ApiKey } from "../../types";

export interface CreateApiKeyRequest {
  name: string;
}

export interface UpdateApiKeyRequest {
  valid: boolean;
}

export interface ApiKeyHttpResponse {
  apiKey: ApiKey;
}

export interface ApiKeysHttpResponse {
  apiKeys?: ApiKey[];
}
