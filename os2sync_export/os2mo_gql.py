# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from typing import Iterable
from uuid import UUID

import structlog
from more_itertools import first
from more_itertools import one
from more_itertools import only
from more_itertools import partition
from pydantic import ValidationError

from os2sync_export.autogenerated_graphql_client.read_user_i_t_accounts import (
    ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids,
)
from os2sync_export.autogenerated_graphql_client.read_user_i_t_accounts import (
    ReadUserITAccountsEmployeesObjectsCurrentItusers,
)
from os2sync_export.autogenerated_graphql_client.read_user_i_t_accounts import (
    ReadUserITAccountsEmployeesObjectsCurrentItusersEmail,
)
from os2sync_export.autogenerated_graphql_client.read_user_i_t_accounts import (
    ReadUserITAccountsEmployeesObjectsCurrentItusersPhone,
)
from os2sync_export.config import Settings
from os2sync_export.depends import GraphQLClient
from os2sync_export.os2sync import OS2SyncClient
from os2sync_export.os2sync_models import Person
from os2sync_export.os2sync_models import Position
from os2sync_export.os2sync_models import User

logger = structlog.stdlib.get_logger()


async def read_fk_users_from_person(
    graphql_client: GraphQLClient, uuid: UUID, it_user_keys: list[str]
) -> tuple[
    list[ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids],
    list[ReadUserITAccountsEmployeesObjectsCurrentItusers],
]:
    it_accounts = await graphql_client.read_user_i_t_accounts(
        uuid=uuid, it_user_keys=it_user_keys
    )
    current_accounts = one(it_accounts.objects).current
    if current_accounts is None:
        return [], []
    fk_accounts = current_accounts.fk_org_uuids
    ad_accounts = current_accounts.itusers
    return fk_accounts, ad_accounts


async def ensure_mo_fk_org_user_exists(
    graphql_client: GraphQLClient,
    os2sync_user: User,
    fk_org_it_users: list[ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids],
):
    fk_org_account = only(
        filter(lambda f: f.external_id == os2sync_user.Uuid, fk_org_it_users)
    )
    if fk_org_account is None:
        # New user, create it-user in MO. This should trigger a new sync of that user.
        pass
    pass


async def delete_fk_org_user(
    fk_org_it_user: ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids,
):
    raise NotImplementedError


def convert_and_filter(
    settings: Settings,
    fk_org_users: list[ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids],
    it_users: list[ReadUserITAccountsEmployeesObjectsCurrentItusers],
) -> tuple[list[User], set[UUID]]:
    # TODO: add filtering for it_users
    delete_fk_org_users = {
        UUID(fk_org_user.external_id)
        for fk_org_user in fk_org_users
        if fk_org_user.user_key not in {a.user_key for a in it_users}
    }
    # Map user-keys to uuids using uuids from FK-org it account if it exists, else use the it-users external id (eg objectGUID)
    fk_org_uuids = {
        it.user_key: UUID(
            only({f.external_id for f in fk_org_users if f.user_key == it.user_key})
            or it.external_id
        )
        for it in it_users
    }
    os2sync_updates = []
    for it_user in it_users:
        try:
            os2sync_updates.append(
                convert_to_os2sync(
                    settings=settings, it=it_user, uuid=fk_org_uuids[it_user.user_key]
                )
            )
        except ValidationError:
            delete_fk_org_users.add(fk_org_uuids[it_user.user_key])

    return os2sync_updates, delete_fk_org_users


async def delete_mo_fk_org_users(
    graphql_client: GraphQLClient, external_id: UUID
) -> None:
    pass


def choose_public_address(
    candidates: Iterable[ReadUserITAccountsEmployeesObjectsCurrentItusersEmail]
    | Iterable[ReadUserITAccountsEmployeesObjectsCurrentItusersPhone],
    priority: list[UUID],
) -> str | None:
    if not candidates:
        return None
    # Filter visibility
    candidates_filtered = [
        c
        for c in candidates
        if c.visibility is None or c.visibility.user_key == "PUBLIC"
    ]

    if priority == []:
        tmp = first(candidates_filtered, default=None)
        return tmp.value if tmp else None

    try:
        tmp = min(
            (c for c in candidates_filtered if c.address_type.uuid in priority),
            key=lambda p: priority.index(p.address_type.uuid),
        )
    except ValueError:
        tmp = None
    return tmp.value if tmp else None


def convert_to_os2sync(
    settings: Settings,
    it: ReadUserITAccountsEmployeesObjectsCurrentItusers,
    uuid: UUID,
) -> User:
    if it.person is None:
        raise ValueError(
            "The given it-account has no 'person' connected and is therefore invalid."
        )
    mo_person = one(it.person)
    cpr = mo_person.cpr_number if settings.sync_cpr else None
    person = Person(Name=mo_person.nickname or mo_person.name, Cpr=cpr)
    landline_candidates, mobile_candidates = partition(
        lambda p: p.address_type.uuid in settings.landline_scope_classes, it.phone
    )
    landline = choose_public_address(
        landline_candidates, settings.landline_scope_classes
    )
    mobile = choose_public_address(mobile_candidates, settings.phone_scope_classes)
    email = choose_public_address(it.email, settings.email_scope_classes)

    positions = [
        Position(
            Name=i.extension_3
            if settings.use_extension_field_as_job_function and i.extension_3
            else i.job_function.name,
            OrgUnitUuid=one(i.org_unit).uuid,
        )
        for i in it.engagement or []
    ]

    return User(
        Uuid=uuid,
        UserId=it.user_key,
        Person=person,
        Positions=positions,
        PhoneNumber=mobile,
        Landline=landline,
        Email=email,
        Location="TODO",
        FMKID=None,
        RacfID=None,
    )


async def sync_mo_user_to_fk_org(
    graphql_client: GraphQLClient,
    settings: Settings,
    os2sync_client: OS2SyncClient,
    uuid: UUID,
):
    fk_org_users, it_users = await read_fk_users_from_person(
        graphql_client=graphql_client,
        uuid=uuid,
        it_user_keys=settings.uuid_from_it_systems,
    )
    logger.info(
        "Found the following itusers",
        uuid=uuid,
        fk_org_users=fk_org_users,
        ad_users=it_users,
    )
    updates_fk, deletes_fk = convert_and_filter(settings, fk_org_users, it_users)
    for os2sync_user in updates_fk:
        await ensure_mo_fk_org_user_exists(graphql_client, os2sync_user, fk_org_users)
        os2sync_client.update_user(os2sync_user)
    for deleted_user_uuid in deletes_fk:
        await delete_mo_fk_org_users(graphql_client, deleted_user_uuid)
        os2sync_client.delete_user(deleted_user_uuid)
