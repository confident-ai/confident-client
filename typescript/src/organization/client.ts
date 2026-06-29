import { Api, Endpoints, HttpMethods } from "../api";
import { Organization } from "../types";
import { OrganizationApiKeys } from "./apiKeys";
import { OrganizationGovernance } from "./governance";
import { OrganizationIam } from "./iam";
import { OrganizationInvitations } from "./invitations";
import { OrganizationMembers } from "./members";
import {
  OrganizationHttpResponse,
  UpdateOrganizationRequest,
} from "./types";

export class OrganizationClient {
  readonly apiKeys: OrganizationApiKeys;
  readonly members: OrganizationMembers;
  readonly invitations: OrganizationInvitations;
  readonly iam: OrganizationIam;
  readonly governance: OrganizationGovernance;

  constructor(private readonly api: Api) {
    this.apiKeys = new OrganizationApiKeys(api);
    this.members = new OrganizationMembers(api);
    this.invitations = new OrganizationInvitations(api);
    this.iam = new OrganizationIam(api);
    this.governance = new OrganizationGovernance(api);
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
