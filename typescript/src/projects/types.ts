import { Project } from "../types";

export interface CreateProjectRequest {
  name: string;
  description?: string;
  email?: string;
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
}

export interface ProjectHttpResponse {
  project: Project;
}

export interface ProjectsHttpResponse {
  projects?: Project[];
}
