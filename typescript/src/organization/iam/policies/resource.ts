import { Api, Endpoints, HttpMethods } from "../../../api";
import { DeletionResult, Policy } from "../../../types";
import {
  PoliciesHttpResponse,
  PolicyHttpResponse,
  PolicyRequest,
} from "./types";

export class OrganizationPolicies {
  constructor(private readonly api: Api) {}

  async list(): Promise<Policy[]> {
    const data = await this.api.sendRequest<PoliciesHttpResponse>(
      HttpMethods.GET,
      Endpoints.ORGANIZATION_POLICIES_ENDPOINT,
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
      Endpoints.ORGANIZATION_POLICIES_ENDPOINT,
      { body },
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
      Endpoints.ORGANIZATION_POLICY_ENDPOINT,
      { body, urlParams: { policyId } },
    );
    return data.policy;
  }

  async delete(policyId: string): Promise<DeletionResult> {
    return this.api.sendRequest<DeletionResult>(
      HttpMethods.DELETE,
      Endpoints.ORGANIZATION_POLICY_ENDPOINT,
      { urlParams: { policyId } },
    );
  }
}
