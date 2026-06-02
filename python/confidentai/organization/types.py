from ..types import ConfidentBaseModel, Organization


class UpdateOrganizationRequest(ConfidentBaseModel):
    name: str


class OrganizationHttpResponse(ConfidentBaseModel):
    organization: Organization


__all__ = [
    "UpdateOrganizationRequest",
    "OrganizationHttpResponse",
]
