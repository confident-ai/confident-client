import { Api } from "../../api";
import { OrganizationGovernancePolicies } from "./policies";

export class OrganizationGovernance {
  readonly policies: OrganizationGovernancePolicies;

  constructor(api: Api) {
    this.policies = new OrganizationGovernancePolicies(api);
  }
}
