import os
from dataclasses import dataclass
from typing import Any

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv():
        return None

load_dotenv()


def _get_config_value(key: str, default: Any = "") -> Any:
    value = os.getenv(key)
    if value not in (None, ""):
        return value
    try:
        import streamlit as st

        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default


@dataclass
class Settings:
    base_url: str
    jwt: str
    sqlite_path: str
    export_path: str
    token_refresh_enabled: bool
    token_refresh_url: str
    token_refresh_method: str
    token_refresh_cookie: str
    token_refresh_headers_json: str
    token_refresh_body_json: str
    token_refresh_min_interval_seconds: int
    github_token: str
    github_repo: str
    github_branch: str
    github_solutions_dir: str


def get_settings() -> Settings:
    return Settings(
        base_url=_get_config_value("JAM_API_BASE", "https://core.proxy.prod.us-west-2.prod.jam.training.aws.dev"),
        jwt=_get_config_value("JAM_API_JWT", ""),
        sqlite_path=_get_config_value("SQLITE_PATH", "./jam_mapper.db"),
        export_path=_get_config_value("EXPORT_PATH", "./exports"),
        token_refresh_enabled=str(_get_config_value("JAM_TOKEN_REFRESH_ENABLED", "false")).lower() == "true",
        token_refresh_url=_get_config_value("JAM_TOKEN_REFRESH_URL", "https://vs.aws.amazon.com/token"),
        token_refresh_method=str(_get_config_value("JAM_TOKEN_REFRESH_METHOD", "POST")).upper(),
        token_refresh_cookie=_get_config_value("JAM_TOKEN_REFRESH_COOKIE", ""),
        token_refresh_headers_json=_get_config_value("JAM_TOKEN_REFRESH_HEADERS_JSON", "{}"),
        token_refresh_body_json=_get_config_value("JAM_TOKEN_REFRESH_BODY_JSON", "{}"),
        token_refresh_min_interval_seconds=int(_get_config_value("JAM_TOKEN_REFRESH_MIN_INTERVAL_SECONDS", "900")),
        github_token=_get_config_value("GITHUB_TOKEN", ""),
        github_repo=_get_config_value("GITHUB_REPO", ""),
        github_branch=_get_config_value("GITHUB_BRANCH", "main"),
        github_solutions_dir=_get_config_value("GITHUB_SOLUTIONS_DIR", "solutions"),
    )


Settings = Settings
