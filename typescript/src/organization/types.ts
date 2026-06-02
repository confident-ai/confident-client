import { Organization } from "../types";

export interface UpdateOrganizationRequest {
  name: string;
}

export interface OrganizationHttpResponse {
  organization: Organization;
}
