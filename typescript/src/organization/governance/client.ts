import { Api } from "../../api";
import { GovernancePolicies } from "./policies";

export class OrganizationGovernance {
  readonly policies: GovernancePolicies;

  constructor(api: Api) {
    this.policies = new GovernancePolicies(api);
  }
}
