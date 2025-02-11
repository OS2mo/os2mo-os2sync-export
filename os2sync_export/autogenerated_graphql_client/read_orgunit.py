# Generated by ariadne-codegen on 2025-02-11 16:39
# Source: queries.graphql

from typing import List
from typing import Optional
from uuid import UUID

from .base_model import BaseModel


class ReadOrgunit(BaseModel):
    org_units: "ReadOrgunitOrgUnits"


class ReadOrgunitOrgUnits(BaseModel):
    objects: List["ReadOrgunitOrgUnitsObjects"]


class ReadOrgunitOrgUnitsObjects(BaseModel):
    current: Optional["ReadOrgunitOrgUnitsObjectsCurrent"]


class ReadOrgunitOrgUnitsObjectsCurrent(BaseModel):
    uuid: UUID
    name: str
    parent: Optional["ReadOrgunitOrgUnitsObjectsCurrentParent"]
    ancestors: List["ReadOrgunitOrgUnitsObjectsCurrentAncestors"]
    unit_type: Optional["ReadOrgunitOrgUnitsObjectsCurrentUnitType"]
    org_unit_level: Optional["ReadOrgunitOrgUnitsObjectsCurrentOrgUnitLevel"]
    org_unit_hierarchy_model: Optional[
        "ReadOrgunitOrgUnitsObjectsCurrentOrgUnitHierarchyModel"
    ]
    addresses: List["ReadOrgunitOrgUnitsObjectsCurrentAddresses"]
    itusers: List["ReadOrgunitOrgUnitsObjectsCurrentItusers"]
    managers: List["ReadOrgunitOrgUnitsObjectsCurrentManagers"]
    kles: List["ReadOrgunitOrgUnitsObjectsCurrentKles"]


class ReadOrgunitOrgUnitsObjectsCurrentParent(BaseModel):
    uuid: UUID
    itusers: List["ReadOrgunitOrgUnitsObjectsCurrentParentItusers"]


class ReadOrgunitOrgUnitsObjectsCurrentParentItusers(BaseModel):
    user_key: str


class ReadOrgunitOrgUnitsObjectsCurrentAncestors(BaseModel):
    uuid: UUID


class ReadOrgunitOrgUnitsObjectsCurrentUnitType(BaseModel):
    uuid: UUID


class ReadOrgunitOrgUnitsObjectsCurrentOrgUnitLevel(BaseModel):
    uuid: UUID


class ReadOrgunitOrgUnitsObjectsCurrentOrgUnitHierarchyModel(BaseModel):
    name: str


class ReadOrgunitOrgUnitsObjectsCurrentAddresses(BaseModel):
    address_type: "ReadOrgunitOrgUnitsObjectsCurrentAddressesAddressType"
    name: Optional[str]


class ReadOrgunitOrgUnitsObjectsCurrentAddressesAddressType(BaseModel):
    scope: Optional[str]
    uuid: UUID
    user_key: str


class ReadOrgunitOrgUnitsObjectsCurrentItusers(BaseModel):
    user_key: str


class ReadOrgunitOrgUnitsObjectsCurrentManagers(BaseModel):
    person: Optional[List["ReadOrgunitOrgUnitsObjectsCurrentManagersPerson"]]


class ReadOrgunitOrgUnitsObjectsCurrentManagersPerson(BaseModel):
    itusers: List["ReadOrgunitOrgUnitsObjectsCurrentManagersPersonItusers"]


class ReadOrgunitOrgUnitsObjectsCurrentManagersPersonItusers(BaseModel):
    external_id: Optional[str]


class ReadOrgunitOrgUnitsObjectsCurrentKles(BaseModel):
    kle_number: List["ReadOrgunitOrgUnitsObjectsCurrentKlesKleNumber"]


class ReadOrgunitOrgUnitsObjectsCurrentKlesKleNumber(BaseModel):
    uuid: UUID


ReadOrgunit.update_forward_refs()
ReadOrgunitOrgUnits.update_forward_refs()
ReadOrgunitOrgUnitsObjects.update_forward_refs()
ReadOrgunitOrgUnitsObjectsCurrent.update_forward_refs()
ReadOrgunitOrgUnitsObjectsCurrentParent.update_forward_refs()
ReadOrgunitOrgUnitsObjectsCurrentParentItusers.update_forward_refs()
ReadOrgunitOrgUnitsObjectsCurrentAncestors.update_forward_refs()
ReadOrgunitOrgUnitsObjectsCurrentUnitType.update_forward_refs()
ReadOrgunitOrgUnitsObjectsCurrentOrgUnitLevel.update_forward_refs()
ReadOrgunitOrgUnitsObjectsCurrentOrgUnitHierarchyModel.update_forward_refs()
ReadOrgunitOrgUnitsObjectsCurrentAddresses.update_forward_refs()
ReadOrgunitOrgUnitsObjectsCurrentAddressesAddressType.update_forward_refs()
ReadOrgunitOrgUnitsObjectsCurrentItusers.update_forward_refs()
ReadOrgunitOrgUnitsObjectsCurrentManagers.update_forward_refs()
ReadOrgunitOrgUnitsObjectsCurrentManagersPerson.update_forward_refs()
ReadOrgunitOrgUnitsObjectsCurrentManagersPersonItusers.update_forward_refs()
ReadOrgunitOrgUnitsObjectsCurrentKles.update_forward_refs()
ReadOrgunitOrgUnitsObjectsCurrentKlesKleNumber.update_forward_refs()
