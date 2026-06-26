from typing import List

from pydantic import Field

from ....types import ConfidentBaseModel, Permission


class PermissionsHttpResponse(ConfidentBaseModel):
    permissions: List[Permission] = Field(default_factory=list)
