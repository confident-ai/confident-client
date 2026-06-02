import { Member } from "../../types";

export interface UpdateMemberRoleRequest {
  roleId: string;
}

export interface MemberHttpResponse {
  member: Member;
}

export interface MembersHttpResponse {
  members?: Member[];
}
