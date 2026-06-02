from typing import List, Optional

from pydantic import Field

from ..types import ConfidentBaseModel, Project


class CreateProjectRequest(ConfidentBaseModel):
    name: str
    description: Optional[str] = None
    email: Optional[str] = None


class UpdateProjectRequest(ConfidentBaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectHttpResponse(ConfidentBaseModel):
    project: Project


class ProjectsHttpResponse(ConfidentBaseModel):
    projects: List[Project] = Field(default_factory=list)


__all__ = [
    "CreateProjectRequest",
    "UpdateProjectRequest",
    "ProjectHttpResponse",
    "ProjectsHttpResponse",
]
