# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
import unittest
from unittest.mock import AsyncMock
from unittest.mock import patch

from fastramqpi.ra_utils.async_to_sync import async_to_sync
from parameterized import parameterized  # type: ignore

from os2sync_export import os2mo
from os2sync_export.os2mo import get_sts_user_raw as os2mo_get_sts_user_raw
from tests.helpers import NICKNAME_TEMPLATE
from tests.helpers import MoEmployeeMixin
from tests.helpers import dummy_positions
from tests.helpers import dummy_settings
from tests.helpers import mock_engagements_to_user


class TestGetStsUser(unittest.TestCase, MoEmployeeMixin):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self._uuid = "mock-uuid"
        self._user_key = "mock-user-key"

    @parameterized.expand(
        [
            # Test without template
            (
                None,  # template config
                dict(nickname=False),  # mo employee response kwargs
                "name",  # key of expected value for `Name`
            ),
            # Test with template: user has no nickname
            (
                {"person.name": NICKNAME_TEMPLATE},  # template config
                dict(nickname=False),  # mo employee response kwargs
                "name",  # key of expected value for `Name`
            ),
            # Test with template: user has a nickname
            (
                {"person.name": NICKNAME_TEMPLATE},  # template config
                dict(nickname=True),  # mo employee response kwargs
                "nickname",  # key of expected value for `Name`
            ),
        ]
    )
    @async_to_sync
    async def test_person_template_nickname(
        self,
        os2sync_templates,
        response_kwargs,
        expected_key,
    ):
        mo_employee_response = self.mock_employee_response(**response_kwargs)
        sts_user = await self._run(
            mo_employee_response,
            ad_user_key=self._user_key,
            os2sync_templates=os2sync_templates,
        )
        self.assertDictEqual(
            sts_user,
            {
                "Email": None,
                "Landline": None,
                "PhoneNumber": None,
                "Uuid": self._uuid,
                "UserId": self._user_key,
                "Positions": dummy_positions,
                "Person": {
                    "Name": mo_employee_response.json()[expected_key],
                    "Cpr": mo_employee_response.json()["cpr_no"],
                },
            },
        )

    @parameterized.expand(
        [
            # Test without an AD BVN and without template
            (
                None,  # template config
                None,  # return value of `try_get_it_user_key`
                "mock-uuid",  # expected value of `UserId` (MO UUID)
            ),
            # Test without an AD BVN, and template which uses `user_key`
            (
                {"person.user_id": "{{ user_key }}"},  # template config
                None,  # return value of `try_get_it_user_key`
                "testtestesen",  # expected value of `UserId` (MO BVN)
            ),
            # Test without an AD BVN, and template which uses `uuid`
            (
                {"person.user_id": "{{ uuid }}"},  # template config
                None,  # return value of `try_get_it_user_key`
                "mock-uuid",  # expected value of `UserId` (MO UUID)
            ),
            # Test with an AD BVN, but without template
            (
                None,  # template config
                "mock-ad-bvn",  # return value of `try_get_it_user_key`
                "mock-ad-bvn",  # expected value of `UserId` (AD BVN)
            ),
            # Test with an AD BVN, and template which uses `user_key`
            (
                {"person.user_id": "{{ user_key }}"},  # template config
                "mock-ad-bvn",  # return value of `try_get_it_user_key`
                "mock-ad-bvn",  # expected value of `UserId` (AD BVN)
            ),
            # Test with an AD BVN, and template which uses `uuid`
            (
                {"person.user_id": "{{ uuid }}"},  # template config
                "mock-ad-bvn",  # return value of `try_get_it_user_key`
                "mock-ad-bvn",  # expected value of `UserId` (AD BVN)
            ),
        ]
    )
    @async_to_sync
    async def test_user_template_user_id(
        self,
        os2sync_templates,
        given_ad_user_key,
        expected_user_id,
    ):
        mo_employee_response = self.mock_employee_response()
        sts_user = await self._run(
            mo_employee_response,
            ad_user_key=given_ad_user_key,
            os2sync_templates=os2sync_templates,
        )
        self.assertDictEqual(
            sts_user,
            {
                "Email": None,
                "Landline": None,
                "PhoneNumber": None,
                "Uuid": self._uuid,
                "UserId": expected_user_id,
                "Positions": dummy_positions,
                "Person": {
                    "Name": mo_employee_response.json()["name"],
                    "Cpr": mo_employee_response.json()["cpr_no"],
                },
            },
        )

    @patch.object(os2mo, "engagements_to_user", mock_engagements_to_user)
    @patch.object(os2mo, "pick_address", return_value=None)
    @patch.object(os2mo, "org_unit_uuids", return_value={})
    async def _run(
        self,
        response,
        address_mock,
        org_unit_uuids_mock,
        ad_user_key=None,
        os2sync_templates=None,
    ):
        settings = dummy_settings
        settings.sync_cpr = True
        settings.templates = os2sync_templates or {}
        gql_mock = AsyncMock()
        with self._patch("os2mo_get", response):
            return await os2mo_get_sts_user_raw(
                self._uuid,
                settings=settings,
                graphql_session=gql_mock,
                fk_org_uuid=None,
                user_key=ad_user_key,
            )

    def _patch(self, name, return_value):
        return patch.object(os2mo, name, return_value=return_value)
