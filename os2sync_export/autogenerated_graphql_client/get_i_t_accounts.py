# Generated by ariadne-codegen on 2024-09-06 13:59
# Source: queries.graphql
from typing import List
from typing import Optional
from uuid import UUID

from .base_model import BaseModel


class GetITAccounts(BaseModel):
    employees: List["GetITAccountsEmployees"]


class GetITAccountsEmployees(BaseModel):
    objects: List["GetITAccountsEmployeesObjects"]


class GetITAccountsEmployeesObjects(BaseModel):
    itusers: List["GetITAccountsEmployeesObjectsItusers"]


class GetITAccountsEmployeesObjectsItusers(BaseModel):
    uuid: UUID
    user_key: str
    engagement_uuid: Optional[UUID]
    itsystem: "GetITAccountsEmployeesObjectsItusersItsystem"


class GetITAccountsEmployeesObjectsItusersItsystem(BaseModel):
    name: str


GetITAccounts.update_forward_refs()
GetITAccountsEmployees.update_forward_refs()
GetITAccountsEmployeesObjects.update_forward_refs()
GetITAccountsEmployeesObjectsItusers.update_forward_refs()
GetITAccountsEmployeesObjectsItusersItsystem.update_forward_refs()
