import { Invitation } from "../../types";

export interface CreateProjectInvitationsRequest {
  emails: string[];
  projectRoleId?: string;
}

export interface InvitationHttpResponse {
  invitation: Invitation;
}

export interface InvitationsHttpResponse {
  invitations?: Invitation[];
}
