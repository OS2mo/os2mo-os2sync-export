# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from uuid import uuid4

from os2sync_export.autogenerated_graphql_client.locate_f_k_user import LocateFKUser
from os2sync_export.cleanup_fk_users import user_is_passive


def test_user_is_passive_no_user():
    """If no MO user is found either by uuid or ituser it counts as passive"""
    user = LocateFKUser(itusers={"objects": []}, employees={"objects": []})
    assert user_is_passive(user)


def test_user_is_passive_active_employee():
    """Check that an employee with an engagement is not considered passive"""
    user = LocateFKUser(
        itusers={"objects": []},
        employees={"objects": [{"current": {"engagements": [{"uuid": uuid4()}]}}]},
    )
    assert not user_is_passive(user)


def test_user_is_passive_passive_employee():
    """Check that an employee with no engagement is considered passive"""
    user = LocateFKUser(
        itusers={"objects": []},
        employees={"objects": [{"current": {"engagements": []}}]},
    )
    assert user_is_passive(user)


def test_user_is_passive_active_ituser():
    """Check that an employee that is found through ituser and has an engagement is not considered passive"""
    user = LocateFKUser(
        itusers={
            "objects": [{"current": {"person": [{"engagements": [{"uuid": uuid4()}]}]}}]
        },
        employees={"objects": []},
    )
    assert not user_is_passive(user)


def test_user_is_passive_passive_ituser():
    """Check that an employee that is found through ituser and has no engagement is considered passive"""
    user = LocateFKUser(
        itusers={"objects": [{"current": {"person": [{"engagements": []}]}}]},
        employees={"objects": []},
    )
    assert user_is_passive(user)
