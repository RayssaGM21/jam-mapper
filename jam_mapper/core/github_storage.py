"""GitHub Contents API storage for Markdown solutions."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Optional

import httpx

from jam_mapper.core.config import get_settings
from jam_mapper.core.solutions import slugify


@dataclass
class GitHubFile:
    path: str
    content: str
    sha: Optional[str]
    html_url: Optional[str]


class GitHubSolutionStorage:
    def __init__(self):
        settings = get_settings()
        self.token = settings.github_token
        self.repo = settings.github_repo
        self.branch = settings.github_branch or "main"
        self.directory = (settings.github_solutions_dir or "solutions").strip("/")
        self.base_url = "https://api.github.com"

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.repo)

    def solution_path(self, challenge_id: str) -> str:
        return f"{self.directory}/{slugify(challenge_id)}.md"

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def read(self, challenge_id: str) -> Optional[GitHubFile]:
        path = self.solution_path(challenge_id)
        url = f"{self.base_url}/repos/{self.repo}/contents/{path}"
        with httpx.Client(timeout=20.0) as client:
            response = client.get(url, headers=self._headers(), params={"ref": self.branch})
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()
        raw_content = payload.get("content") or ""
        content = base64.b64decode(raw_content).decode("utf-8") if raw_content else ""
        return GitHubFile(
            path=path,
            content=content,
            sha=payload.get("sha"),
            html_url=payload.get("html_url"),
        )

    def write(self, challenge_id: str, content: str, message: str, sha: Optional[str] = None) -> GitHubFile:
        path = self.solution_path(challenge_id)
        existing = self.read(challenge_id)
        effective_sha = sha or (existing.sha if existing else None)
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        payload = {
            "message": message,
            "content": encoded,
            "branch": self.branch,
        }
        if effective_sha:
            payload["sha"] = effective_sha

        url = f"{self.base_url}/repos/{self.repo}/contents/{path}"
        with httpx.Client(timeout=20.0) as client:
            response = client.put(url, headers=self._headers(), json=payload)
        response.raise_for_status()
        result = response.json()
        content_payload = result.get("content") or {}
        return GitHubFile(
            path=path,
            content=content,
            sha=content_payload.get("sha"),
            html_url=content_payload.get("html_url"),
        )
