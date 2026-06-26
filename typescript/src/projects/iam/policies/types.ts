import { Policy } from "../../../types";

export interface PolicyRequest {
  name: string;
  permissionIds: string[];
  description?: string;
}

export interface PolicyHttpResponse {
  policy: Policy;
}

export interface PoliciesHttpResponse {
  policies?: Policy[];
}
