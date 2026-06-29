import { Api, Endpoints, HttpMethods } from "../../../api";
import {
  GovernancePolicy,
  GovernancePolicyAssignmentResult,
  GovernancePolicyUnassignmentResult,
  NamedRef,
} from "../../../types";
import {
  GovernancePoliciesHttpResponse,
  GovernancePolicyProjectsHttpResponse,
  ProjectIdsRequest,
} from "./types";

export class OrganizationGovernancePolicies {
  constructor(private readonly api: Api) {}

  async list(): Promise<GovernancePolicy[]> {
    const data = await this.api.sendRequest<GovernancePoliciesHttpResponse>(
      HttpMethods.GET,
      Endpoints.ORGANIZATION_GOVERNANCE_POLICIES_ENDPOINT,
    );
    return data.governancePolicies ?? [];
  }

  async listProjects(
    policyId: string,
    params: { page?: number; pageSize?: number } = {},
  ): Promise<NamedRef[]> {
    const data =
      await this.api.sendRequest<GovernancePolicyProjectsHttpResponse>(
        HttpMethods.GET,
        Endpoints.ORGANIZATION_GOVERNANCE_POLICY_PROJECTS_ENDPOINT,
        {
          params: { page: params.page, pageSize: params.pageSize },
          urlParams: { policyId },
        },
      );
    return data.projects ?? [];
  }

  async assign(
    policyId: string,
    params: ProjectIdsRequest,
  ): Promise<GovernancePolicyAssignmentResult> {
    const body: ProjectIdsRequest = { projectIds: params.projectIds };
    return this.api.sendRequest<GovernancePolicyAssignmentResult>(
      HttpMethods.POST,
      Endpoints.ORGANIZATION_GOVERNANCE_POLICY_ASSIGN_ENDPOINT,
      { body, urlParams: { policyId } },
    );
  }

  async unassign(
    policyId: string,
    params: ProjectIdsRequest,
  ): Promise<GovernancePolicyUnassignmentResult> {
    const body: ProjectIdsRequest = { projectIds: params.projectIds };
    return this.api.sendRequest<GovernancePolicyUnassignmentResult>(
      HttpMethods.POST,
      Endpoints.ORGANIZATION_GOVERNANCE_POLICY_UNASSIGN_ENDPOINT,
      { body, urlParams: { policyId } },
    );
  }
}
