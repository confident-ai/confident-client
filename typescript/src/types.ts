export interface NamedRef {
  id: string;
  name: string;
}

export interface Organization {
  id: string;
  name: string;
  plan?: string;
  created_at?: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string | null;
  organizationId?: string;
  created_at?: string;
  governancePolicy?: NamedRef | null;
}

export interface ApiKey {
  id: number;
  name?: string | null;
  valid: boolean;
  value: string;
  created_at?: string;
  lastUsed?: string | null;
}

export interface CreatedProject {
  project: Project;
  apiKey?: ApiKey;
}

export interface Member {
  id: string;
  email: string;
  name?: string | null;
  image?: string | null;
  organizationRole?: NamedRef | null;
  projectRole?: NamedRef | null;
}

export type InvitationStatus = "PENDING" | "ACCEPTED" | "DECLINED";

export interface Invitation {
  id: number;
  email: string;
  status?: InvitationStatus;
  created_at?: string;
  organizationRoleId?: string | null;
  projectRoleId?: string | null;
}

export interface Role {
  id: string;
  name: string;
  description?: string | null;
  organizationId?: string | null;
  projectId?: string | null;
  policies: NamedRef[];
}

export interface Policy {
  id: string;
  name: string;
  description?: string | null;
  permissions: NamedRef[];
}

export interface Permission {
  id: string;
  name: string;
  description?: string | null;
}

export interface DeletionResult {
  id?: string | number;
  deleted?: boolean;
  removed?: boolean;
}

export type GovernanceControlType =
  | "RUNTIME"
  | "PRE_DEPLOYMENT_EVALS"
  | "PRE_DEPLOYMENT_RED_TEAMING"
  | "OPERATIONAL";

export interface GovernanceControl {
  id: string;
  name: string;
  type: GovernanceControlType;
}

export interface GovernancePolicy {
  id: string;
  name: string;
  description?: string | null;
  projectsCount: number;
  controls: GovernanceControl[];
}

export interface GovernancePolicyAssignmentResult {
  governancePolicy: NamedRef;
  assignedProjectIds: string[];
  notFoundProjectIds: string[];
  count: number;
}

export interface GovernancePolicyUnassignmentResult {
  governancePolicy: NamedRef;
  unassignedProjectIds: string[];
  skippedProjectIds: string[];
  count: number;
}
