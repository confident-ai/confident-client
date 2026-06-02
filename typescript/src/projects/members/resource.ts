import { Api, Endpoints, HttpMethods } from "../../api";
import { DeletionResult, Member } from "../../types";
import {
  MemberHttpResponse,
  MembersHttpResponse,
  UpdateMemberRoleRequest,
} from "./types";

export class ProjectMembers {
  constructor(
    private readonly api: Api,
    private readonly projectId: string,
  ) {}

  async list(params: { page?: number; pageSize?: number } = {}): Promise<
    Member[]
  > {
    const data = await this.api.sendRequest<MembersHttpResponse>(
      HttpMethods.GET,
      Endpoints.PROJECT_MEMBERS_ENDPOINT,
      {
        params: { page: params.page, pageSize: params.pageSize },
        urlParams: { projectId: this.projectId },
      },
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
      Endpoints.PROJECT_MEMBER_ENDPOINT,
      { body, urlParams: { projectId: this.projectId, userId } },
    );
    return data.member;
  }

  async remove(userId: string): Promise<DeletionResult> {
    return this.api.sendRequest<DeletionResult>(
      HttpMethods.DELETE,
      Endpoints.PROJECT_MEMBER_ENDPOINT,
      { urlParams: { projectId: this.projectId, userId } },
    );
  }
}
