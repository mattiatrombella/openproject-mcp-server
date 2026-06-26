"""Live verification for Work / Remaining work (estimatedTime / remainingTime).

Creates a work package, sets estimated/remaining hours via the client, GETs it
back, and asserts the ISO 8601 durations round-trip. Also tests a fractional
value and confirms percentage_done is not unexpectedly wiped.

Requires a live OpenProject instance. Reads credentials from the environment
(same vars the server uses):

    OPENPROJECT_URL        e.g. https://your-instance.openproject.com
    OPENPROJECT_API_KEY    your API key
    OPENPROJECT_PROXY      optional HTTP proxy

Usage:
    # PROJECT_ID and TYPE_ID must exist on your instance (use list_projects / list_types)
    PROJECT_ID=1 TYPE_ID=1 python scripts/verify_work_fields.py

By default the created work package is deleted at the end. Set KEEP=1 to keep it.
"""

import os
import sys
import asyncio

# Allow running from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.client import OpenProjectClient
from src.utils.formatting import (
    hours_to_iso8601_duration,
    iso8601_duration_to_hours,
)


def _client() -> OpenProjectClient:
    base_url = os.getenv("OPENPROJECT_URL")
    api_key = os.getenv("OPENPROJECT_API_KEY")
    proxy = os.getenv("OPENPROJECT_PROXY")
    if not base_url or not api_key:
        sys.exit("ERROR: set OPENPROJECT_URL and OPENPROJECT_API_KEY")
    return OpenProjectClient(base_url, api_key, proxy)


def _check(label: str, got, want) -> bool:
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: got={got!r} want={want!r}")
    return ok


async def main() -> int:
    project_id = int(os.getenv("PROJECT_ID", "0"))
    type_id = int(os.getenv("TYPE_ID", "0"))
    if not project_id or not type_id:
        sys.exit("ERROR: set PROJECT_ID and TYPE_ID (existing IDs on your instance)")

    client = _client()
    failures = 0
    wp_id = None

    try:
        # 1. Create with estimated=16h, remaining=14h
        print("Creating work package with estimatedTime=PT16H, remainingTime=PT14H ...")
        created = await client.create_work_package({
            "project": project_id,
            "subject": "verify_work_fields temp WP",
            "type": type_id,
            "estimatedTime": hours_to_iso8601_duration(16),
            "remainingTime": hours_to_iso8601_duration(14),
        })
        wp_id = created.get("id")
        print(f"Created #{wp_id}")

        # 2. GET back and assert raw ISO durations
        wp = await client.get_work_package(wp_id)
        print("After create:")
        failures += not _check("estimatedTime", wp.get("estimatedTime"), "PT16H")
        failures += not _check("remainingTime", wp.get("remainingTime"), "PT14H")
        print(f"  (derived percentageDone = {wp.get('percentageDone')!r})")

        # 3. Fractional value test: 2.5h -> PT2H30M
        print("\nUpdating estimated_hours=2.5 (expect PT2H30M) ...")
        await client.update_work_package(wp_id, {
            "estimatedTime": hours_to_iso8601_duration(2.5),
        })
        wp = await client.get_work_package(wp_id)
        failures += not _check("estimatedTime", wp.get("estimatedTime"), "PT2H30M")
        failures += not _check(
            "round-trip hours", iso8601_duration_to_hours(wp.get("estimatedTime")), 2.5
        )

        # 4. Confirm setting percentage_done alone doesn't wipe, then check
        #    interdependency note: set percentage_done explicitly.
        print("\nSetting percentage_done=50 alone ...")
        await client.update_work_package(wp_id, {"percentage_done": 50})
        wp = await client.get_work_package(wp_id)
        failures += not _check("percentageDone", wp.get("percentageDone"), 50)
        print(f"  (estimatedTime now = {wp.get('estimatedTime')!r}, "
              f"remainingTime = {wp.get('remainingTime')!r})")

        # 5. Interdependency observation: set both Work + Remaining, report %.
        print("\nSetting estimated=16h + remaining=14h together (watch percentageDone) ...")
        await client.update_work_package(wp_id, {
            "estimatedTime": hours_to_iso8601_duration(16),
            "remainingTime": hours_to_iso8601_duration(14),
        })
        wp = await client.get_work_package(wp_id)
        print(f"  estimatedTime={wp.get('estimatedTime')!r} "
              f"remainingTime={wp.get('remainingTime')!r} "
              f"percentageDone={wp.get('percentageDone')!r} "
              "(API may have derived percentageDone)")

    finally:
        if wp_id and os.getenv("KEEP") != "1":
            try:
                await client.delete_work_package(wp_id)
                print(f"\nDeleted temp #{wp_id} (set KEEP=1 to keep)")
            except Exception as e:
                print(f"\nWARN: cleanup failed for #{wp_id}: {e}")

    print(f"\n{'ALL PASS' if failures == 0 else str(failures) + ' FAILURE(S)'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
