import { Api, Endpoints, HttpMethods } from "../../api";
import { DeletionResult, Invitation } from "../../types";
import {
  CreateProjectInvitationsRequest,
  InvitationHttpResponse,
  InvitationsHttpResponse,
} from "./types";

export class ProjectInvitations {
  constructor(
    private readonly api: Api,
    private readonly projectId: string,
  ) {}

  async list(): Promise<Invitation[]> {
    const data = await this.api.sendRequest<InvitationsHttpResponse>(
      HttpMethods.GET,
      Endpoints.PROJECT_INVITATIONS_ENDPOINT,
      { urlParams: { projectId: this.projectId } },
    );
    return data.invitations ?? [];
  }

  async create(params: {
    emails: string[];
    roleId?: string;
  }): Promise<Invitation[]> {
    const body: CreateProjectInvitationsRequest = { emails: params.emails };
    if (params.roleId !== undefined) {
      body.projectRoleId = params.roleId;
    }
    const data = await this.api.sendRequest<InvitationsHttpResponse>(
      HttpMethods.POST,
      Endpoints.PROJECT_INVITATIONS_ENDPOINT,
      { body, urlParams: { projectId: this.projectId } },
    );
    return data.invitations ?? [];
  }

  async resend(invitationId: number): Promise<Invitation> {
    const data = await this.api.sendRequest<InvitationHttpResponse>(
      HttpMethods.PUT,
      Endpoints.PROJECT_INVITATION_ENDPOINT,
      { urlParams: { projectId: this.projectId, invitationId } },
    );
    return data.invitation;
  }

  async revoke(invitationId: number): Promise<DeletionResult> {
    return this.api.sendRequest<DeletionResult>(
      HttpMethods.DELETE,
      Endpoints.PROJECT_INVITATION_ENDPOINT,
      { urlParams: { projectId: this.projectId, invitationId } },
    );
  }
}
