from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ConfidentBaseModel(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class ApiResponse(ConfidentBaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    deprecated: Optional[bool] = None
    link: Optional[str] = None


class ConfidentApiError(Exception):
    """Custom exception that preserves API response metadata"""

    def __init__(self, message: str, link: Optional[str] = None):
        super().__init__(message)
        self.link = link


class NamedRef(ConfidentBaseModel):
    id: str
    name: str


class Organization(ConfidentBaseModel):
    id: str
    name: str
    plan: Optional[str] = None
    created_at: Optional[str] = None


class Project(ConfidentBaseModel):
    id: str
    name: str
    description: Optional[str] = None
    organization_id: Optional[str] = Field(default=None, alias="organizationId")
    created_at: Optional[str] = None
    governance_policy: Optional[NamedRef] = Field(
        default=None, alias="governancePolicy"
    )


class ApiKey(ConfidentBaseModel):
    id: int
    name: Optional[str] = None
    valid: bool
    value: str
    created_at: Optional[str] = None
    last_used: Optional[str] = Field(default=None, alias="lastUsed")


class CreatedProject(ConfidentBaseModel):
    project: Project
    api_key: Optional[ApiKey] = Field(default=None, alias="apiKey")


class Member(ConfidentBaseModel):
    id: str
    email: str
    name: Optional[str] = None
    image: Optional[str] = None
    organization_role: Optional[NamedRef] = Field(
        default=None, alias="organizationRole"
    )
    project_role: Optional[NamedRef] = Field(default=None, alias="projectRole")


class Invitation(ConfidentBaseModel):
    id: int
    email: str
    status: Optional[str] = None
    created_at: Optional[str] = None
    organization_role_id: Optional[str] = Field(
        default=None, alias="organizationRoleId"
    )
    project_role_id: Optional[str] = Field(default=None, alias="projectRoleId")


class Role(ConfidentBaseModel):
    id: str
    name: str
    description: Optional[str] = None
    organization_id: Optional[str] = Field(default=None, alias="organizationId")
    project_id: Optional[str] = Field(default=None, alias="projectId")
    policies: List[NamedRef] = Field(default_factory=list)


class Policy(ConfidentBaseModel):
    id: str
    name: str
    description: Optional[str] = None
    permissions: List[NamedRef] = Field(default_factory=list)


class Permission(ConfidentBaseModel):
    id: str
    name: str
    description: Optional[str] = None


class DeletionResult(ConfidentBaseModel):
    id: Any = None
    deleted: Optional[bool] = None
    removed: Optional[bool] = None


class GovernanceControl(ConfidentBaseModel):
    id: str
    name: str
    type: str


class GovernancePolicy(ConfidentBaseModel):
    id: str
    name: str
    description: Optional[str] = None
    projects_count: int = Field(default=0, alias="projectsCount")
    controls: List[GovernanceControl] = Field(default_factory=list)


class GovernancePolicyAssignmentResult(ConfidentBaseModel):
    governance_policy: NamedRef = Field(alias="governancePolicy")
    count: int
