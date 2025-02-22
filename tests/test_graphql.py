# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from typing import Callable
from unittest.mock import AsyncMock
from unittest.mock import call
from unittest.mock import patch
from uuid import uuid4

from os2sync_export.config import Settings
from os2sync_export.os2mo import get_sts_user
from os2sync_export.os2mo import group_accounts

mo_uuid = str(uuid4())
engagement_uuid1 = str(uuid4())
engagement_uuid2 = str(uuid4())
fk_org_uuid_1 = str(uuid4())
fk_org_user_key_1 = "AndersA"
fk_org_uuid_2 = str(uuid4())
fk_org_user_key_2 = "AAnd"
fk_org_uuid_3 = str(uuid4())
omada_username = "OmAdA"
ad_username = "saMAcCouNtnAme"

query_response = [
    {
        "uuid": str(uuid4()),
        "user_key": fk_org_uuid_2,
        "engagement_uuid": engagement_uuid2,
        "itsystem": {"name": "FK-ORG UUID"},
    },
    {
        "uuid": str(uuid4()),
        "user_key": fk_org_user_key_1,
        "engagement_uuid": engagement_uuid1,
        "itsystem": {"name": "FK-ORG USERNAME"},
    },
    {
        "uuid": str(uuid4()),
        "user_key": fk_org_uuid_3,
        "engagement_uuid": None,
        "itsystem": {"name": "FK-ORG UUID"},
    },
    {
        "uuid": str(uuid4()),
        "user_key": fk_org_uuid_1,
        "engagement_uuid": engagement_uuid1,
        "itsystem": {"name": "FK-ORG UUID"},
    },
    {
        "uuid": str(uuid4()),
        "user_key": fk_org_user_key_2,
        "engagement_uuid": engagement_uuid2,
        "itsystem": {"name": "FK-ORG USERNAME"},
    },
]


def test_group_by_engagement_noop():
    groups = group_accounts(query_response, [], [])
    assert len(groups) == 3
    for g in groups:
        assert g.get("uuid") is None
        assert g.get("user_key") is None


def test_group_by_engagement():
    groups = group_accounts(query_response, ["FK-ORG UUID"], "FK-ORG USERNAME")
    assert len(groups) == 3

    for g in [
        {"engagement_uuid": None, "user_key": None, "uuid": fk_org_uuid_3},
        {
            "engagement_uuid": engagement_uuid1,
            "user_key": fk_org_user_key_1,
            "uuid": fk_org_uuid_1,
        },
        {
            "engagement_uuid": engagement_uuid2,
            "user_key": fk_org_user_key_2,
            "uuid": fk_org_uuid_2,
        },
    ]:
        assert g in groups


@patch("os2sync_export.os2mo.get_sts_user_raw")
async def test_get_sts_user(
    get_sts_user_raw_mock, set_settings: Callable[..., Settings]
):
    gql_mock = AsyncMock()
    gql_mock.execute.return_value = {
        "employees": {"objects": [{"current": {"itusers": query_response}}]}
    }
    settings = set_settings(
        uuid_from_it_systems=["FK-ORG UUID"],
        user_key_it_system_names=["FK-ORG USERNAME"],
    )
    await get_sts_user(mo_uuid=mo_uuid, graphql_session=gql_mock, settings=settings)

    assert len(get_sts_user_raw_mock.call_args_list) == 3
    for c in [
        call(
            mo_uuid,
            settings=settings,
            graphql_session=gql_mock,
            fk_org_uuid=fk_org_uuid_1,
            user_key=fk_org_user_key_1,
            engagement_uuid=engagement_uuid1,
        ),
        call(
            mo_uuid,
            settings=settings,
            graphql_session=gql_mock,
            fk_org_uuid=fk_org_uuid_2,
            user_key=fk_org_user_key_2,
            engagement_uuid=engagement_uuid2,
        ),
        call(
            mo_uuid,
            settings=settings,
            graphql_session=gql_mock,
            fk_org_uuid=fk_org_uuid_3,
            user_key=None,
            engagement_uuid=None,
        ),
    ]:
        assert c in get_sts_user_raw_mock.call_args_list


@patch("os2sync_export.os2mo.get_sts_user_raw")
async def test_get_sts_user_duplicate_username_no_uuid_itsystem(
    get_sts_user_raw_mock, set_settings: Callable[..., Settings]
):
    """Currently only relevant for Frederikshavn"""
    query_response_frederikshavn = [
        {
            "uuid": str(uuid4()),
            "user_key": fk_org_uuid_2,
            "engagement_uuid": None,
            "itsystem": {"name": "FK-ORG UUID"},
        },
        {
            "uuid": str(uuid4()),
            "user_key": omada_username,
            "engagement_uuid": None,
            "itsystem": {"name": "OMADA USERNAME"},
        },
        {
            "uuid": str(uuid4()),
            "user_key": ad_username,
            "engagement_uuid": None,
            "itsystem": {"name": "AD USERNAME"},
        },
    ]

    gql_mock = AsyncMock()
    gql_mock.execute.return_value = {
        "employees": {
            "objects": [{"current": {"itusers": query_response_frederikshavn}}]
        }
    }
    settings = set_settings(
        uuid_from_it_systems=["FK-ORG UUID"],
        user_key_it_system_names=["OMADA USERNAME", "AD USERNAME"],
    )
    await get_sts_user(mo_uuid=mo_uuid, graphql_session=gql_mock, settings=settings)
    get_sts_user_raw_mock.assert_called_once_with(
        mo_uuid,
        settings=settings,
        graphql_session=gql_mock,
        fk_org_uuid=fk_org_uuid_2,
        user_key=omada_username,
        engagement_uuid=None,
    )


@patch("os2sync_export.os2mo.get_sts_user_raw")
async def test_get_sts_user_no_it_accounts(
    get_sts_user_raw_mock, mock_settings: Settings
):
    """Test that users without it-accounts creates one fk-org account"""
    gql_mock = AsyncMock()
    gql_mock.execute.return_value = {
        "employees": {"objects": [{"current": {"itusers": []}}]}
    }

    await get_sts_user(
        mo_uuid=mo_uuid, graphql_session=gql_mock, settings=mock_settings
    )
    get_sts_user_raw_mock.assert_called_once_with(
        mo_uuid,
        settings=mock_settings,
        graphql_session=gql_mock,
        fk_org_uuid=None,
        user_key=None,
        engagement_uuid=None,
    )
