# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from uuid import UUID

import requests
from tenacity import retry
from tenacity import retry_if_exception_type
from tenacity import stop_after_delay
from tenacity import wait_fixed

from os2sync_export.config import get_os2sync_settings
from os2sync_export.os2sync_models import OrgUnit

retry_max_time = 60
settings = get_os2sync_settings()
logger = logging.getLogger(__name__)


def get_os2sync_session():
    session = requests.Session()

    if settings.os2sync_api_url == "stub":
        from os2sync_export import stub

        session = stub.Session()

    session.verify = settings.os2sync_ca_verify_os2sync
    session.headers["User-Agent"] = "os2mo-data-import-and-export"
    session.headers["CVR"] = settings.municipality
    return session


session = get_os2sync_session()


def os2sync_url(url):
    """format url like {BASE}/user"""
    url = url.format(BASE=settings.os2sync_api_url)
    return url


@retry(
    wait=wait_fixed(5),
    reraise=True,
    stop=stop_after_delay(10 * 60),
    retry=retry_if_exception_type(requests.HTTPError),
)
def os2sync_get(url, **params) -> Dict:
    url = os2sync_url(url)
    r = session.get(url, params=params)
    if r.status_code == 404:
        raise KeyError(f"No object found at {url=}, {params=}")
    r.raise_for_status()
    return r.json()


def os2sync_get_org_unit(api_url: str, uuid: UUID) -> OrgUnit:
    current = os2sync_get(f"{api_url}/orgUnit/{str(uuid)}")
    current.pop("Type")
    current.pop("Timestamp")
    return OrgUnit(**current)


def os2sync_delete(url, **params):
    url = os2sync_url(url)
    try:
        r = session.delete(url, **params)
        r.raise_for_status()
        return r
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning("delete %r %r :404", url, params)
            return r


def os2sync_post(url, **params):
    url = os2sync_url(url)
    r = session.post(url, **params)
    r.raise_for_status()
    return r


def delete_orgunit(uuid: UUID):
    logger.debug("delete orgunit %s", uuid)
    os2sync_delete("{BASE}/orgUnit/" + str(uuid))


def upsert_org_unit(org_unit: OrgUnit, os2sync_api_url: str) -> None:
    try:
        current = os2sync_get_org_unit(api_url=os2sync_api_url, uuid=org_unit.Uuid)
    except KeyError:
        logger.info(f"OrgUnit not found in os2sync - creating {org_unit.Uuid=}")
        os2sync_post("{BASE}/orgUnit/", json=org_unit.json())
        return

    # Avoid overwriting information that we cannot provide from os2mo.
    org_unit.LOSShortName = current.LOSShortName
    org_unit.Tasks = org_unit.Tasks or current.Tasks
    org_unit.ShortKey = org_unit.ShortKey or current.ShortKey
    org_unit.PayoutUnitUuid = org_unit.PayoutUnitUuid or current.PayoutUnitUuid
    org_unit.ContactPlaces = org_unit.ContactPlaces or current.ContactPlaces
    org_unit.ContactOpenHours = org_unit.ContactOpenHours or current.ContactOpenHours

    logger.info(f"Syncing org_unit {org_unit}")

    os2sync_post("{BASE}/orgUnit/", json=org_unit.json())


def trigger_hierarchy(client: requests.Session, os2sync_api_url: str) -> UUID:
    """ "Triggers a job in the os2sync container that gathers the entire hierarchy from FK-ORG

    Returns: UUID

    """
    r = client.get(f"{os2sync_api_url}/hierarchy")
    r.raise_for_status()
    return UUID(r.text)


@retry(
    wait=wait_fixed(5),
    reraise=True,
    stop=stop_after_delay(10 * 60),
    retry=retry_if_exception_type(requests.HTTPError),
)
def get_hierarchy(
    client: requests.Session, os2sync_api_url: str, request_uuid: UUID
) -> Tuple[Set[UUID], Set[UUID]]:
    """Fetches the hierarchy from os2sync. Retries for 10 minutes until it is ready."""
    r = client.get(f"{os2sync_api_url}/hierarchy/{str(request_uuid)}")
    r.raise_for_status()
    hierarchy = r.json()["Result"]
    if hierarchy is None:
        raise ConnectionError("Check connection to FK-ORG")
    existing_os2sync_org_units = {UUID(o["Uuid"]) for o in hierarchy["OUs"]}
    existing_os2sync_users = {UUID(u["Uuid"]) for u in hierarchy["Users"]}
    return existing_os2sync_org_units, existing_os2sync_users


def update_single_orgunit(uuid: UUID, org_unit: Optional[OrgUnit]):
    if org_unit:
        upsert_org_unit(
            org_unit,
            settings.os2sync_api_url,
        )
    else:
        delete_orgunit(uuid)


def update_single_user(users: List[Optional[Dict[str, Any]]]):
    for sts_user in users:
        if sts_user:
            os2sync_post("{BASE}/user", json=sts_user)
