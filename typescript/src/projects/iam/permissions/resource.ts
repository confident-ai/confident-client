import { Api, Endpoints, HttpMethods } from "../../../api";
import { Permission } from "../../../types";
import { PermissionsHttpResponse } from "./types";

export class ProjectPermissions {
  constructor(
    private readonly api: Api,
    private readonly projectId: string,
  ) {}

  async list(): Promise<Permission[]> {
    const data = await this.api.sendRequest<PermissionsHttpResponse>(
      HttpMethods.GET,
      Endpoints.PROJECT_PERMISSIONS_ENDPOINT,
      { urlParams: { projectId: this.projectId } },
    );
    return data.permissions ?? [];
  }
}
