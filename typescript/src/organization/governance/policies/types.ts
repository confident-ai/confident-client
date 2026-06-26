import { GovernancePolicy } from "../../../types";

export interface AssignProjectsRequest {
  projectIds: string[];
}

export interface GovernancePoliciesHttpResponse {
  governancePolicies?: GovernancePolicy[];
}
