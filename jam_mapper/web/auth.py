"""Authentication gate for the Streamlit application.

The preferred production mode is Streamlit OIDC. A local, secret-backed login is
provided for small private deployments where configuring an identity provider is
not practical. There is deliberately no public sign-up flow.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from typing import Any

import streamlit as st

from jam_mapper.core.config import _get_config_value


PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 600_000


@dataclass(frozen=True)
class AuthenticatedUser:
    email: str
    name: str


def _rerun() -> None:
    """Rerun on both current and legacy Streamlit releases."""
    rerun = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if not callable(rerun):
        raise RuntimeError("Esta versão do Streamlit não oferece suporte a rerun.")
    rerun()


def _normalized_email(value: Any) -> str:
    return str(value or "").strip().casefold()


def _allowed_emails() -> set[str]:
    raw = _get_config_value("APP_ALLOWED_EMAILS", "")
    values = raw if isinstance(raw, (list, tuple)) else str(raw).split(",")
    return {_normalized_email(value) for value in values if _normalized_email(value)}


def _local_users() -> dict[str, dict[str, str]]:
    raw = _get_config_value("APP_USERS_JSON", "{}")
    try:
        payload = raw if isinstance(raw, dict) else json.loads(str(raw))
    except (TypeError, ValueError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return {
        _normalized_email(email): details
        for email, details in payload.items()
        if _normalized_email(email) and isinstance(details, dict)
    }


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    """Create a secrets-compatible PBKDF2 password hash."""
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations, salt_b64, digest_b64 = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
        actual = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError):
        return False


def _render_login_shell(title: str, help_text: str) -> None:
    st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)
    left, center, right = st.columns([1, 1.25, 1])
    with center:
        st.title(title)
        st.caption(help_text)


def _require_oidc() -> AuthenticatedUser:
    if not st.user.is_logged_in:
        _render_login_shell("Acesso restrito", "Entre com o e-mail previamente autorizado.")
        _, center, _ = st.columns([1, 1.25, 1])
        with center:
            if st.button("Entrar", type="primary", use_container_width=True):
                st.login()
        st.stop()

    email = _normalized_email(getattr(st.user, "email", ""))
    if not email or email not in _allowed_emails():
        _render_login_shell("Acesso não autorizado", "Este e-mail não está liberado para acessar o painel.")
        _, center, _ = st.columns([1, 1.25, 1])
        with center:
            if st.button("Sair", use_container_width=True):
                st.logout()
        st.stop()
    return AuthenticatedUser(email=email, name=str(getattr(st.user, "name", "") or email))


def _require_local() -> AuthenticatedUser:
    authenticated = st.session_state.get("authenticated_user")
    if isinstance(authenticated, dict) and authenticated.get("email"):
        return AuthenticatedUser(email=authenticated["email"], name=authenticated.get("name") or authenticated["email"])

    _render_login_shell("Acesso restrito", "Use as credenciais cadastradas pelo administrador.")
    _, center, _ = st.columns([1, 1.25, 1])
    with center, st.form("login_form", clear_on_submit=False):
        email = st.text_input("E-mail").strip()
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)

    if submitted:
        normalized = _normalized_email(email)
        user = _local_users().get(normalized, {})
        allowed = _allowed_emails()
        if normalized in allowed and verify_password(password, user.get("password_hash", "")):
            st.session_state.authenticated_user = {"email": normalized, "name": user.get("name") or normalized}
            st.session_state.login_attempts = 0
            _rerun()
        st.session_state.login_attempts = int(st.session_state.get("login_attempts", 0)) + 1
        if normalized not in allowed:
            st.error("Este e-mail não está autorizado para acessar o app local.")
        else:
            st.error("E-mail ou senha inválidos. Verifique a senha cadastrada para este usuário.")
    st.stop()


def require_authenticated_user() -> AuthenticatedUser:
    mode = str(_get_config_value("APP_AUTH_MODE", "oidc")).strip().lower()
    if not _allowed_emails():
        st.error(
            "Autenticação ainda não configurada. No terminal, execute "
            "`python scripts/configure_local_auth.py` e reinicie a aplicação."
        )
        st.stop()
    if mode == "oidc":
        return _require_oidc()
    if mode == "local":
        return _require_local()
    st.error("APP_AUTH_MODE deve ser 'oidc' ou 'local'.")
    st.stop()


def logout() -> None:
    mode = str(_get_config_value("APP_AUTH_MODE", "oidc")).strip().lower()
    if mode == "oidc":
        st.logout()
    for key in ("authenticated_user", "aws_session_ready", "login_attempts"):
        st.session_state.pop(key, None)
    _rerun()
