import { Api, Endpoints, HttpMethods } from "../../../api";
import { Permission } from "../../../types";
import { PermissionsHttpResponse } from "./types";

export class OrganizationPermissions {
  constructor(private readonly api: Api) {}

  async list(): Promise<Permission[]> {
    const data = await this.api.sendRequest<PermissionsHttpResponse>(
      HttpMethods.GET,
      Endpoints.ORGANIZATION_PERMISSIONS_ENDPOINT,
    );
    return data.permissions ?? [];
  }
}
