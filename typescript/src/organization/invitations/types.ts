import { Invitation } from "../../types";

export interface CreateOrganizationInvitationsRequest {
  emails: string[];
  organizationRoleId?: string;
}

export interface InvitationHttpResponse {
  invitation: Invitation;
}

export interface InvitationsHttpResponse {
  invitations?: Invitation[];
}
