import { Api, Endpoints, HttpMethods } from "../../api";
import { DeletionResult, Member } from "../../types";
import {
  MemberHttpResponse,
  MembersHttpResponse,
  UpdateMemberRoleRequest,
} from "./types";

export class OrganizationMembers {
  constructor(private readonly api: Api) {}

  async list(params: { page?: number; pageSize?: number } = {}): Promise<
    Member[]
  > {
    const data = await this.api.sendRequest<MembersHttpResponse>(
      HttpMethods.GET,
      Endpoints.ORGANIZATION_MEMBERS_ENDPOINT,
      { params: { page: params.page, pageSize: params.pageSize } },
    );
    return data.members ?? [];
  }

  async updateRole(
    userId: string,
    params: UpdateMemberRoleRequest,
  ): Promise<Member> {
    const body: UpdateMemberRoleRequest = { roleId: params.roleId };
    const data = await this.api.sendRequest<MemberHttpResponse>(
      HttpMethods.PUT,
      Endpoints.ORGANIZATION_MEMBER_ENDPOINT,
      { body, urlParams: { userId } },
    );
    return data.member;
  }

  async remove(userId: string): Promise<DeletionResult> {
    return this.api.sendRequest<DeletionResult>(
      HttpMethods.DELETE,
      Endpoints.ORGANIZATION_MEMBER_ENDPOINT,
      { urlParams: { userId } },
    );
  }
}
