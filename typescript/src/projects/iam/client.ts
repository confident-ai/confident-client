import { Api } from "../../api";
import { ProjectPermissions } from "./permissions";
import { ProjectPolicies } from "./policies";
import { ProjectRoles } from "./roles";

export class ProjectIam {
  readonly policies: ProjectPolicies;
  readonly roles: ProjectRoles;
  readonly permissions: ProjectPermissions;

  constructor(api: Api, projectId: string) {
    this.policies = new ProjectPolicies(api, projectId);
    this.roles = new ProjectRoles(api, projectId);
    this.permissions = new ProjectPermissions(api, projectId);
  }
}
