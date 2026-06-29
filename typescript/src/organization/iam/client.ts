import { Api } from "../../api";
import { OrganizationPermissions } from "./permissions";
import { OrganizationPolicies } from "./policies";
import { OrganizationRoles } from "./roles";

export class OrganizationIam {
  readonly policies: OrganizationPolicies;
  readonly roles: OrganizationRoles;
  readonly permissions: OrganizationPermissions;

  constructor(api: Api) {
    this.policies = new OrganizationPolicies(api);
    this.roles = new OrganizationRoles(api);
    this.permissions = new OrganizationPermissions(api);
  }
}
