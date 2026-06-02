import { Api, Endpoints, HttpMethods } from "../../api";
import { DeletionResult, Policy } from "../../types";
import {
  PoliciesHttpResponse,
  PolicyHttpResponse,
  PolicyRequest,
} from "./types";

export class ProjectPolicies {
  constructor(
    private readonly api: Api,
    private readonly projectId: string,
  ) {}

  async list(): Promise<Policy[]> {
    const data = await this.api.sendRequest<PoliciesHttpResponse>(
      HttpMethods.GET,
      Endpoints.PROJECT_POLICIES_ENDPOINT,
      { urlParams: { projectId: this.projectId } },
    );
    return data.policies ?? [];
  }

  async create(params: PolicyRequest): Promise<Policy> {
    const body: PolicyRequest = {
      name: params.name,
      permissionIds: params.permissionIds,
      description: params.description,
    };
    const data = await this.api.sendRequest<PolicyHttpResponse>(
      HttpMethods.POST,
      Endpoints.PROJECT_POLICIES_ENDPOINT,
      { body, urlParams: { projectId: this.projectId } },
    );
    return data.policy;
  }

  async update(policyId: string, params: PolicyRequest): Promise<Policy> {
    const body: PolicyRequest = {
      name: params.name,
      permissionIds: params.permissionIds,
      description: params.description,
    };
    const data = await this.api.sendRequest<PolicyHttpResponse>(
      HttpMethods.PUT,
      Endpoints.PROJECT_POLICY_ENDPOINT,
      { body, urlParams: { projectId: this.projectId, policyId } },
    );
    return data.policy;
  }

  async delete(policyId: string): Promise<DeletionResult> {
    return this.api.sendRequest<DeletionResult>(
      HttpMethods.DELETE,
      Endpoints.PROJECT_POLICY_ENDPOINT,
      { urlParams: { projectId: this.projectId, policyId } },
    );
  }
}
