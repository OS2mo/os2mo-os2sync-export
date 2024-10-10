# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from typing import Literal
from typing import cast
from uuid import UUID

import structlog
from fastramqpi.config import Settings as _FastRAMQPISettings
from fastramqpi.ramqp.config import AMQPConnectionSettings as _AMQPConnectionSettings
from pydantic import AnyHttpUrl
from pydantic import BaseSettings

logger = structlog.stdlib.get_logger()


# https://git.magenta.dk/rammearkitektur/FastRAMQPI#multilayer-exchanges
class AMQPConnectionSettings(_AMQPConnectionSettings):
    upstream_exchange = "os2mo"
    exchange = "os2sync_export"
    queue_prefix = "os2sync-export"
    prefetch_count = 1


class FastRAMQPISettings(_FastRAMQPISettings):
    amqp: AMQPConnectionSettings


class Settings(BaseSettings):  # type: ignore
    fastramqpi: FastRAMQPISettings
    # common:

    municipality: str  # Called "municipality.cvr" in settings.json

    # os2sync:
    top_unit_uuid: UUID
    os2sync_api_url: AnyHttpUrl | Literal["stub"] = cast(
        AnyHttpUrl, "http://os2sync:5000/api"
    )

    sync_cpr: bool = False

    autowash: bool = False
    ca_verify_os2sync: bool = True
    ca_verify_os2mo: bool = True

    phone_scope_classes: list[UUID] = []
    landline_scope_classes: list[UUID] = []
    email_scope_classes: list[UUID] = []
    ignored_unit_levels: list[UUID] = []
    ignored_unit_types: list[UUID] = []
    templates: dict = {}

    sync_managers: bool = False
    use_contact_for_tasks: bool = False
    employee_engagement_address: list[str] = []
    uuid_from_it_systems: list[str] = []

    truncate_length: int = 200

    user_key_it_system_names: list[str] = ["Active Directory"]

    filter_hierarchy_names: list[str] = []  # Title in MO
    filter_users_by_it_system: bool = False

    use_extension_field_as_job_function: bool = False

    filter_orgunit_uuid: list[UUID] = []

    enable_kle: bool = True
    # This flag toggles the new integration which uses a completely different than the old integration
    # Use only when it-users exists in mo with the new format, eg:
    # AD-accounts having samaccountname in user_key, ObjectGUID as external_id and addresses and engagements attached to the it-user.
    new: bool = False
    # Sync it-accounts from itsystems with these user_keys:
    # Only relevant when new=True
    it_system_user_keys: list[str] = ["Active Directory"]

    class Config:
        frozen = False
        env_nested_delimiter = "__"

        env_file_encoding = "utf-8"


def get_os2sync_settings(*args, **kwargs) -> Settings:
    return Settings(*args, **kwargs)


if __name__ == "__main__":
    print(get_os2sync_settings())
