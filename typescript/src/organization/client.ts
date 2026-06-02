import { Api, Endpoints, HttpMethods } from "../api";
import { Organization } from "../types";
import { OrganizationApiKeys } from "./apiKeys";
import { OrganizationInvitations } from "./invitations";
import { OrganizationMembers } from "./members";
import { OrganizationPermissions } from "./permissions";
import { OrganizationPolicies } from "./policies";
import { OrganizationRoles } from "./roles";
import {
  OrganizationHttpResponse,
  UpdateOrganizationRequest,
} from "./types";

export class OrganizationClient {
  readonly apiKeys: OrganizationApiKeys;
  readonly members: OrganizationMembers;
  readonly invitations: OrganizationInvitations;
  readonly roles: OrganizationRoles;
  readonly policies: OrganizationPolicies;
  readonly permissions: OrganizationPermissions;

  constructor(private readonly api: Api) {
    this.apiKeys = new OrganizationApiKeys(api);
    this.members = new OrganizationMembers(api);
    this.invitations = new OrganizationInvitations(api);
    this.roles = new OrganizationRoles(api);
    this.policies = new OrganizationPolicies(api);
    this.permissions = new OrganizationPermissions(api);
  }

  async get(): Promise<Organization> {
    const data = await this.api.sendRequest<OrganizationHttpResponse>(
      HttpMethods.GET,
      Endpoints.ORGANIZATION_ENDPOINT,
    );
    return data.organization;
  }

  async update(params: UpdateOrganizationRequest): Promise<Organization> {
    const body: UpdateOrganizationRequest = { name: params.name };
    const data = await this.api.sendRequest<OrganizationHttpResponse>(
      HttpMethods.PUT,
      Endpoints.ORGANIZATION_ENDPOINT,
      { body },
    );
    return data.organization;
  }
}
