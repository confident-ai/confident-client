import { Api, Endpoints, HttpMethods } from "../../api";
import { DeletionResult, Invitation } from "../../types";
import {
  CreateOrganizationInvitationsRequest,
  InvitationHttpResponse,
  InvitationsHttpResponse,
} from "./types";

export class OrganizationInvitations {
  constructor(private readonly api: Api) {}

  async list(): Promise<Invitation[]> {
    const data = await this.api.sendRequest<InvitationsHttpResponse>(
      HttpMethods.GET,
      Endpoints.ORGANIZATION_INVITATIONS_ENDPOINT,
    );
    return data.invitations ?? [];
  }

  async create(params: {
    emails: string[];
    roleId?: string;
  }): Promise<Invitation[]> {
    const body: CreateOrganizationInvitationsRequest = {
      emails: params.emails,
    };
    if (params.roleId !== undefined) {
      body.organizationRoleId = params.roleId;
    }
    const data = await this.api.sendRequest<InvitationsHttpResponse>(
      HttpMethods.POST,
      Endpoints.ORGANIZATION_INVITATIONS_ENDPOINT,
      { body },
    );
    return data.invitations ?? [];
  }

  async resend(invitationId: number): Promise<Invitation> {
    const data = await this.api.sendRequest<InvitationHttpResponse>(
      HttpMethods.PUT,
      Endpoints.ORGANIZATION_INVITATION_ENDPOINT,
      { urlParams: { invitationId } },
    );
    return data.invitation;
  }

  async revoke(invitationId: number): Promise<DeletionResult> {
    return this.api.sendRequest<DeletionResult>(
      HttpMethods.DELETE,
      Endpoints.ORGANIZATION_INVITATION_ENDPOINT,
      { urlParams: { invitationId } },
    );
  }
}
