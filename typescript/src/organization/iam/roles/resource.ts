import { Api, Endpoints, HttpMethods } from "../../../api";
import { DeletionResult, Role } from "../../../types";
import { RoleHttpResponse, RoleRequest, RolesHttpResponse } from "./types";

export class OrganizationRoles {
  constructor(private readonly api: Api) {}

  async list(): Promise<Role[]> {
    const data = await this.api.sendRequest<RolesHttpResponse>(
      HttpMethods.GET,
      Endpoints.ORGANIZATION_ROLES_ENDPOINT,
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
      Endpoints.ORGANIZATION_ROLES_ENDPOINT,
      { body },
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
      Endpoints.ORGANIZATION_ROLE_ENDPOINT,
      { body, urlParams: { roleId } },
    );
    return data.role;
  }

  async delete(roleId: string): Promise<DeletionResult> {
    return this.api.sendRequest<DeletionResult>(
      HttpMethods.DELETE,
      Endpoints.ORGANIZATION_ROLE_ENDPOINT,
      { urlParams: { roleId } },
    );
  }
}
