import { Api, Endpoints, HttpMethods } from "../../../api";
import { DeletionResult, Role } from "../../../types";
import { RoleHttpResponse, RoleRequest, RolesHttpResponse } from "./types";

export class ProjectRoles {
  constructor(
    private readonly api: Api,
    private readonly projectId: string,
  ) {}

  async list(): Promise<Role[]> {
    const data = await this.api.sendRequest<RolesHttpResponse>(
      HttpMethods.GET,
      Endpoints.PROJECT_ROLES_ENDPOINT,
      { urlParams: { projectId: this.projectId } },
    );
    return data.roles ?? [];
  }

  async create(params: RoleRequest): Promise<Role> {
    const body: RoleRequest = {
      name: params.name,
      policyIds: params.policyIds,
      description: params.description,
    };
    const data = await this.api.sendRequest<RoleHttpResponse>(
      HttpMethods.POST,
      Endpoints.PROJECT_ROLES_ENDPOINT,
      { body, urlParams: { projectId: this.projectId } },
    );
    return data.role;
  }

  async update(roleId: string, params: RoleRequest): Promise<Role> {
    const body: RoleRequest = {
      name: params.name,
      policyIds: params.policyIds,
      description: params.description,
    };
    const data = await this.api.sendRequest<RoleHttpResponse>(
      HttpMethods.PUT,
      Endpoints.PROJECT_ROLE_ENDPOINT,
      { body, urlParams: { projectId: this.projectId, roleId } },
    );
    return data.role;
  }

  async delete(roleId: string): Promise<DeletionResult> {
    return this.api.sendRequest<DeletionResult>(
      HttpMethods.DELETE,
      Endpoints.PROJECT_ROLE_ENDPOINT,
      { urlParams: { projectId: this.projectId, roleId } },
    );
  }
}
