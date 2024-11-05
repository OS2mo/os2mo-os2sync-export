# Generated by ariadne-codegen on 2024-11-05 09:14
# Source: queries.graphql

from typing import List
from uuid import UUID

from .base_model import BaseModel


class FindFKItsystem(BaseModel):
    itsystems: "FindFKItsystemItsystems"


class FindFKItsystemItsystems(BaseModel):
    objects: List["FindFKItsystemItsystemsObjects"]


class FindFKItsystemItsystemsObjects(BaseModel):
    uuid: UUID


FindFKItsystem.update_forward_refs()
FindFKItsystemItsystems.update_forward_refs()
FindFKItsystemItsystemsObjects.update_forward_refs()
