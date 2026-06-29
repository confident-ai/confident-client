import { GovernancePolicy, NamedRef } from "../../../types";

export interface ProjectIdsRequest {
  projectIds: string[];
}

export interface GovernancePoliciesHttpResponse {
  governancePolicies?: GovernancePolicy[];
}

export interface GovernancePolicyProjectsHttpResponse {
  projects?: NamedRef[];
}
