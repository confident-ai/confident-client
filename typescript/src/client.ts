import { Api } from "./api";
import { OrganizationClient } from "./organization/client";
import { ProjectClient, ProjectsClient } from "./projects/client";
import { Organization } from "./types";

export interface ConfidentAIOptions {
  apiKey?: string;
  baseUrl?: string;
  timeout?: number;
}

export class ConfidentAI {
  readonly apiKey: string;
  readonly baseUrl: string;
  readonly projects: ProjectsClient;
  private readonly api: Api;

  constructor(options: ConfidentAIOptions = {}) {
    this.api = new Api({
      apiKey: options.apiKey,
      baseUrl: options.baseUrl,
      timeout: options.timeout,
    });
    this.apiKey = this.api.apiKey;
    this.baseUrl = this.api.baseUrl;
    this.projects = new ProjectsClient(this.api);
  }

  organization(): OrganizationClient {
    return new OrganizationClient(this.api);
  }

  project(projectId: string): ProjectClient {
    return new ProjectClient(this.api, projectId);
  }

  whoami(): Promise<Organization> {
    return this.organization().get();
  }
}
