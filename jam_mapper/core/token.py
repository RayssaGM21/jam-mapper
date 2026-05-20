"""Token refresh helpers with local rate limiting."""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

import httpx

from jam_mapper.core.config import get_settings
from jam_mapper.core.db import Database


TOKEN_SETTING_KEY = "runtime_authorization_token"
TOKEN_REFRESH_TS_KEY = "runtime_authorization_token_last_refresh"


def _json_env(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _extract_token(payload: Dict[str, Any]) -> Optional[str]:
    for key in ["authorization", "Authorization", "accessToken", "access_token", "idToken", "id_token", "jwt", "token"]:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    for value in payload.values():
        if isinstance(value, dict):
            nested = _extract_token(value)
            if nested:
                return nested
    return None


def get_cached_authorization_token() -> str:
    return Database().get_setting(TOKEN_SETTING_KEY, "")


def refresh_authorization_token(force: bool = False) -> str:
    """Refresh authorization token if configured and outside the minimum interval."""
    settings = get_settings()
    if not settings.token_refresh_enabled:
        return ""

    db = Database()
    now = int(time.time())
    last_refresh = int(db.get_setting(TOKEN_REFRESH_TS_KEY, 0) or 0)
    if not force and now - last_refresh < settings.token_refresh_min_interval_seconds:
        return db.get_setting(TOKEN_SETTING_KEY, "")

    db.set_setting(TOKEN_REFRESH_TS_KEY, now)
    headers = _json_env(settings.token_refresh_headers_json)
    body = _json_env(settings.token_refresh_body_json)
    if settings.token_refresh_cookie and "cookie" not in {key.lower() for key in headers}:
        headers["Cookie"] = settings.token_refresh_cookie
    headers.setdefault("Accept", "application/json")

    with httpx.Client(timeout=20.0) as client:
        if body:
            response = client.post(settings.token_refresh_url, headers=headers, json=body)
        else:
            response = client.post(settings.token_refresh_url, headers=headers)
        response.raise_for_status()
        payload = response.json()

    token = _extract_token(payload)
    if not token:
        raise ValueError("Token refresh response did not contain a recognizable token field.")

    db.set_setting(TOKEN_SETTING_KEY, token)
    return token
