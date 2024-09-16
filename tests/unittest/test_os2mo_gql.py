# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import patch
from uuid import uuid4

from os2sync_export.autogenerated_graphql_client.read_user_i_t_accounts import (
    ReadUserITAccountsEmployees,
)
from os2sync_export.os2mo_gql import sync_mo_user_to_fk_org


@patch("os2sync_export.os2mo_gql.update_fk_org_user")
async def test_sync_mo_user_to_fk_no_users(update_mock, graphql_client, mock_settings):
    graphql_client.read_user_i_t_accounts.return_value = ReadUserITAccountsEmployees(
        **{"objects": [{"current": None}]}
    )
    await sync_mo_user_to_fk_org(
        graphql_client=graphql_client, uuid=uuid4(), settings=mock_settings
    )
    update_mock.assert_not_called()


@patch("os2sync_export.os2mo_gql.delete_fk_org_user")
@patch("os2sync_export.os2mo_gql.update_fk_org_user")
async def test_sync_mo_user_to_fk_one_it_user(
    update_mock, delete_mock, graphql_client, mock_settings
):
    it_users = ReadUserITAccountsEmployees(
        **{
            "objects": [
                {
                    "current": {
                        "AD_users": [
                            {
                                "uuid": uuid4(),
                                "user_key": str(uuid4()),
                                "external_id": str(uuid4),
                            }
                        ],
                        "fk_org_users": [],
                    }
                }
            ]
        }
    )
    graphql_client.read_user_i_t_accounts.return_value = it_users
    await sync_mo_user_to_fk_org(
        graphql_client=graphql_client, uuid=uuid4(), settings=mock_settings
    )
    delete_mock.assert_not_called()
    update_mock.assert_called_once_with(it_users.objects[0].current.a_d_users[0], None)


@patch("os2sync_export.os2mo_gql.delete_fk_org_user")
@patch("os2sync_export.os2mo_gql.update_fk_org_user")
async def test_sync_mo_user_to_fk_delete_user(
    update_mock, delete_mock, graphql_client, mock_settings
):
    it_users = ReadUserITAccountsEmployees(
        **{
            "objects": [
                {
                    "current": {
                        "AD_users": [],
                        "fk_org_users": [
                            {
                                "user_key": str(uuid4()),
                                "external_id": str(uuid4),
                            }
                        ],
                    }
                }
            ]
        }
    )
    graphql_client.read_user_i_t_accounts.return_value = it_users
    await sync_mo_user_to_fk_org(
        graphql_client=graphql_client, uuid=uuid4(), settings=mock_settings
    )
    update_mock.assert_not_called()
    delete_mock.assert_called_once_with(it_users.objects[0].current.fk_org_users[0])