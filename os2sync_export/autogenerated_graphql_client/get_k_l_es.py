# Generated by ariadne-codegen on 2024-09-06 13:59
# Source: queries.graphql
from typing import List
from uuid import UUID

from .base_model import BaseModel


class GetKLEs(BaseModel):
    kles: List["GetKLEsKles"]


class GetKLEsKles(BaseModel):
    objects: List["GetKLEsKlesObjects"]


class GetKLEsKlesObjects(BaseModel):
    org_unit_uuid: UUID


GetKLEs.update_forward_refs()
GetKLEsKles.update_forward_refs()
GetKLEsKlesObjects.update_forward_refs()
