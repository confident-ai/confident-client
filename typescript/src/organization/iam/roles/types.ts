import { Role } from "../../../types";

export interface RoleRequest {
  name: string;
  policyIds: string[];
  description?: string;
}

export interface RoleHttpResponse {
  role: Role;
}

export interface RolesHttpResponse {
  roles?: Role[];
}
