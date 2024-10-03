# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import patch
from uuid import UUID
from uuid import uuid4

import pytest
from more_itertools import one

from os2sync_export.autogenerated_graphql_client.read_orgunit import (
    ReadOrgunitOrgUnitsObjectsCurrent,
)
from os2sync_export.autogenerated_graphql_client.read_user_i_t_accounts import (
    ReadUserITAccountsEmployees,
)
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
    ReadUserITAccountsEmployeesObjectsCurrentItusersEngagement,
)
from os2sync_export.autogenerated_graphql_client.read_user_i_t_accounts import (
    ReadUserITAccountsEmployeesObjectsCurrentItusersPerson,
)
from os2sync_export.autogenerated_graphql_client.read_user_i_t_accounts import (
    ReadUserITAccountsEmployeesObjectsCurrentItusersPhone,
)
from os2sync_export.os2mo_gql import choose_public_address
from os2sync_export.os2mo_gql import convert_and_filter
from os2sync_export.os2mo_gql import convert_to_os2sync
from os2sync_export.os2mo_gql import filter_relevant_orgunit
from os2sync_export.os2mo_gql import find_phone_numbers
from os2sync_export.os2mo_gql import mo_orgunit_to_os2sync
from os2sync_export.os2mo_gql import sync_mo_user_to_fk_org

BASE_ITUSER_RESPONSE = ReadUserITAccountsEmployeesObjectsCurrentItusers(
    uuid=uuid4(),
    user_key="test",
    external_id=str(uuid4()),
    email=[],
    phone=[],
    person=[
        ReadUserITAccountsEmployeesObjectsCurrentItusersPerson(
            name="Brian", nickname="", cpr_number=None
        )
    ],
    engagement=[
        ReadUserITAccountsEmployeesObjectsCurrentItusersEngagement(
            **{"job_function": {"name": "tester"}, "org_unit": [{"uuid": uuid4()}]}  # type: ignore
        )
    ],
)


@patch("os2sync_export.os2mo_gql.ensure_mo_fk_org_user_exists")
async def test_sync_mo_user_to_fk_no_users(
    update_mock, graphql_client, mock_settings, os2sync_client
):
    graphql_client.read_user_i_t_accounts.return_value = ReadUserITAccountsEmployees(
        **{"objects": [{"current": None}]}
    )
    await sync_mo_user_to_fk_org(
        graphql_client=graphql_client,
        uuid=uuid4(),
        settings=mock_settings,
        os2sync_client=os2sync_client,
    )
    update_mock.assert_not_called()


async def test_sync_mo_user_to_fk_one_it_user(
    graphql_client, mock_settings, os2sync_client
):
    it_users = ReadUserITAccountsEmployees(
        **{
            "objects": [
                {
                    "current": {
                        "itusers": [
                            {
                                "uuid": uuid4(),
                                "user_key": "BSG",
                                "external_id": str(uuid4()),
                                "phone": [
                                    {
                                        "address_type": {
                                            "uuid": uuid4(),
                                            "scope": "PHONE",
                                        },
                                        "visibility": {"user_key": "PUBLIC"},
                                        "value": "11223344",
                                    }
                                ],
                                "email": [
                                    {
                                        "address_type": {
                                            "uuid": uuid4(),
                                            "scope": "EMAIL",
                                        },
                                        "visibility": {"user_key": "PUBLIC"},
                                        "value": "bsg@digital-identity.dk",
                                    }
                                ],
                                "person": [
                                    {
                                        "name": "Brian Storm Graversen",
                                        "nickname": "",
                                        "cpr_number": 1234567890,
                                    }
                                ],
                                "engagement": [
                                    {
                                        "org_unit": [{"uuid": uuid4()}],
                                        "job_function": {
                                            "name": "open source developer"
                                        },
                                    }
                                ],
                            }
                        ],
                        "fk_org_uuids": [],
                    }
                }
            ]
        }
    )
    graphql_client.read_user_i_t_accounts.return_value = it_users
    await sync_mo_user_to_fk_org(
        graphql_client=graphql_client,
        uuid=uuid4(),
        settings=mock_settings,
        os2sync_client=os2sync_client,
    )
    os2sync_client.delete_user.assert_not_called()
    ituser = it_users.objects[0].current.itusers[0]
    os2sync_client.update_user.assert_called_once_with(
        convert_to_os2sync(mock_settings, ituser, UUID(ituser.external_id))
    )


async def test_sync_mo_user_to_fk_delete_user(
    graphql_client, mock_settings, os2sync_client
):
    it_users = ReadUserITAccountsEmployees(
        **{
            "objects": [
                {
                    "current": {
                        "itusers": [],
                        "fk_org_uuids": [
                            {
                                "user_key": str(uuid4()),
                                "external_id": str(uuid4()),
                            }
                        ],
                    }
                }
            ]
        }
    )
    graphql_client.read_user_i_t_accounts.return_value = it_users
    await sync_mo_user_to_fk_org(
        graphql_client=graphql_client,
        uuid=uuid4(),
        settings=mock_settings,
        os2sync_client=os2sync_client,
    )
    os2sync_client.update_user.assert_not_called()
    os2sync_client.delete_user.assert_called_once_with(
        UUID(it_users.objects[0].current.fk_org_uuids[0].external_id)
    )


def test_convert_to_os2sync(mock_settings):
    mo_it_user = BASE_ITUSER_RESPONSE.copy()
    mo_it_user.person = [
        ReadUserITAccountsEmployeesObjectsCurrentItusersPerson(
            name="Brian", nickname=""
        )
    ]
    os2sync_user = convert_to_os2sync(
        mock_settings, mo_it_user, UUID(mo_it_user.external_id)
    )
    assert os2sync_user.Person.Name == "Brian"


def test_convert_to_os2sync_nickname(mock_settings):
    mo_it_user = BASE_ITUSER_RESPONSE.copy()
    mo_it_user.person = [
        ReadUserITAccountsEmployeesObjectsCurrentItusersPerson(
            name="Brian", nickname="STORMEN"
        )
    ]
    os2sync_user = convert_to_os2sync(
        mock_settings, mo_it_user, UUID(mo_it_user.external_id)
    )
    assert os2sync_user.Person.Name == "STORMEN"


@pytest.mark.parametrize("sync_cpr", [True, False])
def test_convert_to_os2sync_cpr(sync_cpr, set_settings):
    settings = set_settings(sync_cpr=sync_cpr)
    mo_it_user = BASE_ITUSER_RESPONSE.copy()
    mo_it_user.person = [
        ReadUserITAccountsEmployeesObjectsCurrentItusersPerson(
            name="Brian", nickname="STORMEN", cpr_number="1234567890"
        )
    ]
    os2sync_user = convert_to_os2sync(
        settings, mo_it_user, UUID(mo_it_user.external_id)
    )
    if sync_cpr:
        assert os2sync_user.Person.Cpr == "1234567890"
    else:
        assert os2sync_user.Person.Cpr is None


@pytest.mark.parametrize("use_extension_field_as_job_function", [True, False])
def test_convert_to_os2sync_extension_job_function(
    use_extension_field_as_job_function, set_settings
):
    settings = set_settings(
        use_extension_field_as_job_function=use_extension_field_as_job_function
    )
    mo_it_user = BASE_ITUSER_RESPONSE.copy()
    mo_it_user.engagement = [
        ReadUserITAccountsEmployeesObjectsCurrentItusersEngagement(
            **{
                "extension_3": "Konge",
                "org_unit": [{"uuid": uuid4()}],
                "job_function": {"name": "Udvikler"},
            }
        )
    ]
    os2sync_user = convert_to_os2sync(
        settings, mo_it_user, UUID(mo_it_user.external_id)
    )
    if use_extension_field_as_job_function:
        assert os2sync_user.Positions[0].Name == "Konge"
    else:
        assert os2sync_user.Positions[0].Name == "Udvikler"


def test_convert_and_filter_same_uuid(mock_settings):
    """Tests that with an ituser and fk-org user with the same external id, that id is used for os2sync"""
    user_key = "SamAccountName"
    it_user = BASE_ITUSER_RESPONSE.copy()
    it_user.user_key = user_key
    fk_org_user = ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids(
        external_id=it_user.external_id, user_key=user_key
    )
    os2sync_update, os2sync_delete = convert_and_filter(
        settings=mock_settings, it_users=[it_user], fk_org_users=[fk_org_user]
    )
    assert one(os2sync_update).Uuid == UUID(fk_org_user.external_id)
    assert os2sync_delete == set()


def test_convert_and_filter_different_uuid(mock_settings):
    """Tests that with an ituser and fk-org user with different external ids, the id from fk-org system is used for os2sync"""
    user_key = "SamAccountName"
    it_user = BASE_ITUSER_RESPONSE.copy()
    it_user.user_key = user_key
    fk_org_user = ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids(
        external_id=str(uuid4()), user_key=user_key
    )
    os2sync_update, os2sync_delete = convert_and_filter(
        settings=mock_settings, it_users=[it_user], fk_org_users=[fk_org_user]
    )
    assert one(os2sync_update).Uuid == UUID(fk_org_user.external_id)
    assert os2sync_delete == set()


def test_convert_and_filter_no_fk_user(mock_settings):
    """Tests that with an ituser and not fk-org user the it-users external id is used for os2sync"""
    user_key = "SamAccountName"
    it_user = BASE_ITUSER_RESPONSE.copy()
    it_user.user_key = user_key
    os2sync_update, os2sync_delete = convert_and_filter(
        settings=mock_settings, it_users=[it_user], fk_org_users=[]
    )
    assert one(os2sync_update).Uuid == UUID(it_user.external_id)
    assert os2sync_delete == set()


def test_convert_and_filter_no_ituser(mock_settings):
    """Tests that with an fk-org user exists but no ituser, the fk-org account is deleted"""
    user_key = "SamAccountName"
    fk_org_user = ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids(
        external_id=str(uuid4()), user_key=user_key
    )
    os2sync_update, os2sync_delete = convert_and_filter(
        settings=mock_settings, it_users=[], fk_org_users=[fk_org_user]
    )
    assert os2sync_update == []
    assert os2sync_delete == set([UUID(fk_org_user.external_id)])


def test_convert_and_filter_different_user_key(mock_settings):
    """Tests that when two different accounts exists in fk-org-users and it-users the new ituser is used for os2sync, and the old fk-org account is deleted"""
    it_user = BASE_ITUSER_RESPONSE.copy()
    it_user.user_key = "user_key_1"
    fk_org_user = ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids(
        external_id=str(uuid4()), user_key="user_key_2"
    )
    os2sync_update, os2sync_delete = convert_and_filter(
        settings=mock_settings, it_users=[it_user], fk_org_users=[fk_org_user]
    )
    assert one(os2sync_update).Uuid == UUID(it_user.external_id)
    assert os2sync_delete == set([UUID(fk_org_user.external_id)])


def test_convert_and_filter_no_engagement(mock_settings):
    """Tests that when an account has no engagements it is deleted"""
    user_key = "SamAccountName"
    it_user = BASE_ITUSER_RESPONSE.copy()
    fk_org_user = ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids(
        external_id=str(uuid4()), user_key=user_key
    )
    it_user.user_key = user_key
    it_user.engagement = []
    os2sync_update, os2sync_delete = convert_and_filter(
        settings=mock_settings, it_users=[it_user], fk_org_users=[fk_org_user]
    )
    assert os2sync_update == []
    assert os2sync_delete == set(
        [UUID(fk_org_user.external_id)],
    )


ADDRESS_TYPE_UUID = uuid4()


@pytest.mark.parametrize(
    "emails,priority,expected",
    [
        (
            # no email
            [],
            [],
            None,
        ),
        (
            # One email, no priority, no visibility - choose it.
            [
                ReadUserITAccountsEmployeesObjectsCurrentItusersEmail(
                    **{"value": "email@example.com", "address_type": {"uuid": uuid4()}}
                )
            ],
            [],
            "email@example.com",
        ),
        (
            # two emails, choose correct by priority
            [
                ReadUserITAccountsEmployeesObjectsCurrentItusersEmail(
                    **{"value": "wrong", "address_type": {"uuid": uuid4()}}
                ),
                ReadUserITAccountsEmployeesObjectsCurrentItusersEmail(
                    **{"value": "correct", "address_type": {"uuid": ADDRESS_TYPE_UUID}}
                ),
            ],
            [ADDRESS_TYPE_UUID],
            "correct",
        ),
        (
            # two emails, none have a correct priority, choose the first
            [
                ReadUserITAccountsEmployeesObjectsCurrentItusersEmail(
                    **{"value": "first", "address_type": {"uuid": uuid4()}}
                ),
                ReadUserITAccountsEmployeesObjectsCurrentItusersEmail(
                    **{"value": "second", "address_type": {"uuid": uuid4()}}
                ),
            ],
            [ADDRESS_TYPE_UUID],
            "first",
        ),
        (
            # two emails, choose correct by visibility
            [
                ReadUserITAccountsEmployeesObjectsCurrentItusersEmail(
                    **{
                        "value": "wrong",
                        "address_type": {"uuid": ADDRESS_TYPE_UUID},
                        "visibility": {"user_key": "SECRET"},
                    }
                ),
                ReadUserITAccountsEmployeesObjectsCurrentItusersEmail(
                    **{
                        "value": "correct",
                        "address_type": {"uuid": ADDRESS_TYPE_UUID},
                        "visibility": {"user_key": "PUBLIC"},
                    }
                ),
            ],
            [ADDRESS_TYPE_UUID],
            "correct",
        ),
    ],
)
def test_choose_address_emails(emails, priority, expected):
    value = choose_public_address(emails, priority)
    assert value == expected


@pytest.mark.parametrize(
    "phones,landline_classes,mobile_classes,expected_landline,expected_mobile",
    [
        (
            # Only one phonenumber, no priority classes, choose it as mobile
            [
                ReadUserITAccountsEmployeesObjectsCurrentItusersPhone(
                    **{"value": "mobile-number", "address_type": {"uuid": uuid4()}}
                )
            ],
            [],
            [],
            None,
            "mobile-number",
        ),
        (
            # split mobile and landline correctly by classes
            [
                ReadUserITAccountsEmployeesObjectsCurrentItusersPhone(
                    **{"value": "mobile-number", "address_type": {"uuid": uuid4()}}
                ),
                ReadUserITAccountsEmployeesObjectsCurrentItusersPhone(
                    **{
                        "value": "landline-number",
                        "address_type": {"uuid": ADDRESS_TYPE_UUID},
                    }
                ),
            ],
            [ADDRESS_TYPE_UUID],
            [],
            "landline-number",
            "mobile-number",
        ),
    ],
)
def test_choose_address_phone_numbers(
    phones,
    landline_classes,
    mobile_classes,
    expected_landline,
    expected_mobile,
):
    landline, mobile = find_phone_numbers(phones, landline_classes, mobile_classes)
    assert landline == expected_landline
    assert mobile == expected_mobile


## Tests for filter relevant orgunit
TOP_UUID = uuid4()


def test_filter_relevant_orgunit_Unit1(set_settings):
    """Test that the unit matching the uuid in settings is synced"""

    settings = set_settings(top_unit_uuid=TOP_UUID)
    orgunit = ReadOrgunitOrgUnitsObjectsCurrent(
        uuid=TOP_UUID,
        name="root",
        ancestors=[],
        addresses=[],
        itusers=[],
        managers=[],
        kles=[],
    )
    assert filter_relevant_orgunit(settings=settings, orgunit_data=orgunit)


def test_filter_relevant_orgunit_wrong_root(set_settings):
    """Test that a unit with no parents that isn't the unit specified in settings is not synced"""
    settings = set_settings(top_unit_uuid=uuid4())
    orgunit = ReadOrgunitOrgUnitsObjectsCurrent(
        uuid=uuid4(),
        name="root2",
        ancestors=[],
        addresses=[],
        itusers=[],
        managers=[],
        kles=[],
    )
    assert not filter_relevant_orgunit(settings=settings, orgunit_data=orgunit)


def test_filter_relevant_orgunit_ancestor(set_settings):
    """test that units in the correct part of the tree - having the top unit as one of its ancestors- is synced"""
    settings = set_settings(top_unit_uuid=TOP_UUID)
    orgunit = ReadOrgunitOrgUnitsObjectsCurrent(
        uuid=uuid4(),
        parent={"uuid": uuid4(), "itusers": []},
        name="Unit1",
        ancestors=[{"uuid": TOP_UUID}],
        addresses=[],
        itusers=[],
        managers=[],
        kles=[],
    )
    assert filter_relevant_orgunit(settings=settings, orgunit_data=orgunit)


def test_filter_relevant_orgunit_wrong_ancestor(set_settings):
    """Test that units in the wrong part of the tree - not having the top unit as one of its ancestors - are not synced"""
    settings = set_settings(top_unit_uuid=uuid4())
    orgunit = ReadOrgunitOrgUnitsObjectsCurrent(
        uuid=uuid4(),
        parent={"uuid": uuid4(), "itusers": []},
        name="Unit1",
        ancestors=[{"uuid": uuid4()}],
        addresses=[],
        itusers=[],
        managers=[],
        kles=[],
    )
    assert not filter_relevant_orgunit(settings=settings, orgunit_data=orgunit)


def test_filter_relevant_orgunit_hierarchy(set_settings):
    """Test that units belonging to the specified org unit hierarchy is synced"""

    settings = set_settings(
        top_unit_uuid=TOP_UUID, filter_hierarchy_names=["linjeorganisation", "Ekstern"]
    )
    orgunit = ReadOrgunitOrgUnitsObjectsCurrent(
        uuid=uuid4(),
        parent={"uuid": uuid4(), "itusers": []},
        org_unit_hierarchy_model={"name": "linjeorganisation"},
        name="Unit1",
        ancestors=[{"uuid": TOP_UUID}],
        addresses=[],
        itusers=[],
        managers=[],
        kles=[],
    )
    assert filter_relevant_orgunit(settings=settings, orgunit_data=orgunit)


def test_filter_relevant_orgunit_wrong_hierarchy(set_settings):
    """Test that units belonging to the another org unit hierarchy is not synced"""
    settings = set_settings(
        top_unit_uuid=TOP_UUID, filter_hierarchy_names=["linjeorganisation", "Ekstern"]
    )
    orgunit = ReadOrgunitOrgUnitsObjectsCurrent(
        uuid=uuid4(),
        parent={"uuid": uuid4(), "itusers": []},
        org_unit_hierarchy_model={"name": "En helt anden"},
        name="Unit1",
        ancestors=[{"uuid": TOP_UUID}],
        addresses=[],
        itusers=[],
        managers=[],
        kles=[],
    )
    assert not filter_relevant_orgunit(settings=settings, orgunit_data=orgunit)


def test_filter_relevant_orgunit_no_hierarchy_settings(set_settings):
    """Test that if the setting is unset the unit is synced regardless of hierarchy"""
    settings = set_settings(top_unit_uuid=TOP_UUID, filter_hierarchy_names=[])
    orgunit = ReadOrgunitOrgUnitsObjectsCurrent(
        uuid=uuid4(),
        parent={"uuid": uuid4(), "itusers": []},
        org_unit_hierarchy_model={"name": "En helt anden"},
        name="Unit1",
        ancestors=[{"uuid": TOP_UUID}],
        addresses=[],
        itusers=[],
        managers=[],
        kles=[],
    )
    assert filter_relevant_orgunit(settings=settings, orgunit_data=orgunit)


def test_filter_relevant_orgunit_filtered(set_settings):
    """Test that the unit can be filtered in settings"""
    filtered_uuid = uuid4()
    settings = set_settings(top_unit_uuid=TOP_UUID, filter_orgunit_uuid=[filtered_uuid])
    orgunit = ReadOrgunitOrgUnitsObjectsCurrent(
        uuid=filtered_uuid,
        parent={"uuid": uuid4(), "itusers": []},
        org_unit_hierarchy_model={"name": "N/A"},
        name="Unit1",
        ancestors=[{"uuid": TOP_UUID}],
        addresses=[],
        itusers=[],
        managers=[],
        kles=[],
    )
    assert not filter_relevant_orgunit(settings=settings, orgunit_data=orgunit)


def test_filter_relevant_orgunit_filtered_ancestor(set_settings):
    """Test that the unit is not synced if one of its ancestors is filtered in settings"""
    filtered_uuid = uuid4()
    settings = set_settings(top_unit_uuid=TOP_UUID, filter_orgunit_uuid=[filtered_uuid])
    orgunit = ReadOrgunitOrgUnitsObjectsCurrent(
        uuid=uuid4(),
        parent={"uuid": uuid4(), "itusers": []},
        name="Unit1",
        ancestors=[{"uuid": TOP_UUID}, {"uuid": filtered_uuid}],
        addresses=[],
        itusers=[],
        managers=[],
        kles=[],
    )
    assert not filter_relevant_orgunit(settings=settings, orgunit_data=orgunit)


def test_filter_relevant_orgunit_filtered_level(set_settings):
    """Test that the unit is not synced if the org_unit_level is filtered in settings"""
    filtered_level_uuid = uuid4()
    settings = set_settings(
        top_unit_uuid=TOP_UUID, ignored_unit_levels=[filtered_level_uuid]
    )
    orgunit = ReadOrgunitOrgUnitsObjectsCurrent(
        uuid=uuid4(),
        parent={"uuid": uuid4(), "itusers": []},
        name="Unit1",
        ancestors=[{"uuid": TOP_UUID}],
        org_unit_level={"uuid": filtered_level_uuid},
        addresses=[],
        itusers=[],
        managers=[],
        kles=[],
    )
    assert not filter_relevant_orgunit(settings=settings, orgunit_data=orgunit)


def test_filter_relevant_orgunit_filtered_unit_type(set_settings):
    """Test that the unit is not synced if the unit_type is filtered in settings"""
    filtered_unit_type_uuid = uuid4()
    settings = set_settings(
        top_unit_uuid=TOP_UUID, ignored_unit_types=[filtered_unit_type_uuid]
    )
    orgunit = ReadOrgunitOrgUnitsObjectsCurrent(
        uuid=uuid4(),
        parent={"uuid": uuid4(), "itusers": []},
        name="Unit1",
        ancestors=[{"uuid": TOP_UUID}],
        unit_type={"uuid": filtered_unit_type_uuid},
        addresses=[],
        itusers=[],
        managers=[],
        kles=[],
    )
    assert not filter_relevant_orgunit(settings=settings, orgunit_data=orgunit)


def test_mo_orgunit_to_os2sync_fk_org_uuids(mock_settings):
    """Test that the uuids can be overwritten by fk-org it-accounts"""
    fk_org_uuid = uuid4()
    parent_fk_org_uuid = uuid4()
    orgunit = ReadOrgunitOrgUnitsObjectsCurrent(
        uuid=uuid4(),
        parent={"uuid": uuid4(), "itusers": [{"user_key": str(parent_fk_org_uuid)}]},
        name="Unit1",
        ancestors=[{"uuid": mock_settings.top_unit_uuid}],
        addresses=[],
        itusers=[{"user_key": str(fk_org_uuid)}],
        managers=[],
        kles=[],
    )
    unit = mo_orgunit_to_os2sync(mock_settings, orgunit)
    assert unit.Uuid == fk_org_uuid
    assert unit.ParentOrgUnitUuid == parent_fk_org_uuid


@pytest.mark.parametrize("enable_kle", [True, False])
def test_mo_orgunit_to_os2sync_kle_numbers(enable_kle, set_settings):
    """Test that the klenumbers can be written to tasks"""
    settings = set_settings(enable_kle=enable_kle)
    kle_numbers = {uuid4() for i in range(10)}
    orgunit = ReadOrgunitOrgUnitsObjectsCurrent(
        uuid=uuid4(),
        parent={"uuid": uuid4(), "itusers": []},
        name="Unit1",
        ancestors=[{"uuid": settings.top_unit_uuid}],
        addresses=[],
        itusers=[],
        managers=[],
        kles=[{"kle_number": {"uuid": k}} for k in kle_numbers],
    )
    unit = mo_orgunit_to_os2sync(settings, orgunit)
    if enable_kle:
        assert unit.Tasks == kle_numbers
    else:
        assert unit.Tasks == set()
