"""Sync orchestration for AWS Jam catalog and event reports."""

from __future__ import annotations

import logging
from time import time
from typing import Any, Dict, Iterable, List

from jam_mapper.core.client import JamClient
from jam_mapper.core.db import Database
from jam_mapper.core.exporter import export_to_xlsx
from jam_mapper.core.normalizer import normalize_challenge

logger = logging.getLogger("jam_mapper.sync")


def sync_challenges(full: bool = True, limit: int = 6000, offset: int = 0) -> Dict[str, Any]:
    client = JamClient()
    db = Database()
    payload = client.list_challenges(limit=limit, offset=offset)
    now = int(time() * 1000)
    challenges = []
    detail_errors = []

    for item in payload.get("challenges", []):
        base = normalize_challenge(item)
        challenge_id = base.get("challengeId")
        normalized = base

        if full and challenge_id:
            try:
                details = client.get_challenge(challenge_id)
                normalized = normalize_challenge(details)
            except Exception as exc:
                detail_errors.append({"challengeId": challenge_id, "error": str(exc)})
                logger.warning("Failed to fetch details for %s: %s", challenge_id, exc)

        if not normalized.get("challengeId"):
            continue

        db.upsert_challenge(normalized["challengeId"], normalized, last_synced=now)
        challenges.append(normalized)

    xlsx = export_to_xlsx(challenges)
    return {
        "imported": len(challenges),
        "xlsx": xlsx,
        "detailErrors": detail_errors,
    }


def sync_event_reports(event_ids: Iterable[str]) -> Dict[str, Any]:
    client = JamClient()
    db = Database()
    now = int(time() * 1000)
    imported = 0
    errors = []

    for event_id in event_ids:
        if not event_id:
            continue
        try:
            report = client.get_event_report(event_id)
            db.upsert_event_report(event_id, report, now)
            imported += 1
        except Exception as exc:
            errors.append({"eventId": event_id, "error": str(exc)})

    return {"imported": imported, "errors": errors}
