import httpx
import logging
from typing import Any, Dict, List
from jam_mapper.core.config import get_settings
from jam_mapper.core.token import get_cached_authorization_token, refresh_authorization_token

logger = logging.getLogger("jam_mapper.client")


class JamClient:
    def __init__(self, base_url: str | None = None, jwt: str | None = None):
        s = get_settings()
        self.base_url = base_url or s.base_url
        self.jwt = jwt or s.jwt or get_cached_authorization_token()
        self._client = httpx.Client(timeout=30.0)

    def _headers(self) -> Dict[str, str]:
        hdr = {"Accept": "application/json"}
        if self.jwt:
            hdr["authorization"] = self.jwt
        return hdr

    def _get_json(self, url: str) -> Dict[str, Any]:
        logger.debug("GET %s", url)
        response = self._client.get(url, headers=self._headers())
        if response.status_code == 401:
            try:
                refreshed = refresh_authorization_token(force=False)
            except Exception as exc:
                logger.info("Token refresh failed after 401: %s", exc)
                refreshed = ""
            if refreshed and refreshed != self.jwt:
                self.jwt = refreshed
                response = self._client.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()

    def list_challenges(self, limit: int = 6000, offset: int = 0) -> Dict[str, Any]:
        url = f"{self.base_url}/admin/challenges?excludeFields=%2A.props.learningOutcome%2C%2A.lastEditedBy%2C%2A.lastUpdatedBy%2C%2A.lastSuccessfulDeployment%2C%2A.recentSolveTimes%2C%2A.nextSteps&includeArchived=false&limit={limit}&offset={offset}&silent=true"
        return self._get_json(url)

    def get_challenge(self, challenge_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/admin/challenges/{challenge_id}"
        return self._get_json(url)

    def list_events_past(self) -> Dict[str, Any]:
        url = f"{self.base_url}/game/participant/events/past"
        return self._get_json(url)

    def get_event_report(self, event_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/game/participant/event/{event_id}/report"
        return self._get_json(url)
