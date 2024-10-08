# Generated by ariadne-codegen on 2024-09-06 13:59
# Source: queries.graphql
from typing import List
from typing import Optional
from uuid import UUID

from .base_model import BaseModel


class GetItUser(BaseModel):
    itusers: List["GetItUserItusers"]


class GetItUserItusers(BaseModel):
    objects: List["GetItUserItusersObjects"]


class GetItUserItusersObjects(BaseModel):
    employee_uuid: Optional[UUID]
    org_unit_uuid: Optional[UUID]


GetItUser.update_forward_refs()
GetItUserItusers.update_forward_refs()
GetItUserItusersObjects.update_forward_refs()
