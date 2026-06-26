import { GovernancePolicy, NamedRef } from "../../../types";

export interface AssignProjectsRequest {
  projectIds: string[];
}

export interface GovernancePoliciesHttpResponse {
  governancePolicies?: GovernancePolicy[];
}

export interface GovernancePolicyProjectsHttpResponse {
  projects?: NamedRef[];
}
