import { Api, Endpoints, HttpMethods } from "../api";
import { CreatedProject, DeletionResult, Project } from "../types";
import { ProjectApiKeys } from "./apiKeys";
import { ProjectInvitations } from "./invitations";
import { ProjectMembers } from "./members";
import { ProjectPermissions } from "./permissions";
import { ProjectPolicies } from "./policies";
import { ProjectRoles } from "./roles";
import {
  CreateProjectRequest,
  ProjectHttpResponse,
  ProjectsHttpResponse,
  UpdateProjectRequest,
} from "./types";

export class ProjectsClient {
  constructor(private readonly api: Api) {}

  async list(): Promise<Project[]> {
    const data = await this.api.sendRequest<ProjectsHttpResponse>(
      HttpMethods.GET,
      Endpoints.PROJECTS_ENDPOINT,
    );
    return data.projects ?? [];
  }

  async create(params: CreateProjectRequest): Promise<CreatedProject> {
    const body: CreateProjectRequest = {
      name: params.name,
      description: params.description,
      email: params.email,
    };
    return this.api.sendRequest<CreatedProject>(
      HttpMethods.POST,
      Endpoints.PROJECTS_ENDPOINT,
      { body },
    );
  }
}

export class ProjectClient {
  readonly projectId: string;
  readonly apiKeys: ProjectApiKeys;
  readonly members: ProjectMembers;
  readonly invitations: ProjectInvitations;
  readonly roles: ProjectRoles;
  readonly policies: ProjectPolicies;
  readonly permissions: ProjectPermissions;
  private readonly api: Api;

  constructor(api: Api, projectId: string) {
    if (!projectId) {
      throw new Error("projectId is required");
    }
    this.api = api;
    this.projectId = projectId;
    this.apiKeys = new ProjectApiKeys(api, projectId);
    this.members = new ProjectMembers(api, projectId);
    this.invitations = new ProjectInvitations(api, projectId);
    this.roles = new ProjectRoles(api, projectId);
    this.policies = new ProjectPolicies(api, projectId);
    this.permissions = new ProjectPermissions(api, projectId);
  }

  async get(): Promise<Project> {
    const data = await this.api.sendRequest<ProjectHttpResponse>(
      HttpMethods.GET,
      Endpoints.PROJECT_ENDPOINT,
      { urlParams: { projectId: this.projectId } },
    );
    return data.project;
  }

  async update(params: {
    name?: string;
    description?: string;
  }): Promise<Project> {
    const body: UpdateProjectRequest = {
      name: params.name,
      description: params.description,
    };
    const data = await this.api.sendRequest<ProjectHttpResponse>(
      HttpMethods.PUT,
      Endpoints.PROJECT_ENDPOINT,
      { body, urlParams: { projectId: this.projectId } },
    );
    return data.project;
  }

  delete(): Promise<DeletionResult> {
    return this.api.sendRequest<DeletionResult>(
      HttpMethods.DELETE,
      Endpoints.PROJECT_ENDPOINT,
      { urlParams: { projectId: this.projectId } },
    );
  }
}
