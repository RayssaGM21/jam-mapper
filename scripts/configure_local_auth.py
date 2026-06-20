"""Create the private Streamlit secrets file for local authentication."""

from __future__ import annotations

import json
import sys
from getpass import getpass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from jam_mapper.web.auth import hash_password


SECRETS_PATH = PROJECT_ROOT / ".streamlit" / "secrets.toml"


def _toml_string(value: str) -> str:
    # A JSON string uses quoting/escaping compatible with TOML basic strings.
    return json.dumps(value, ensure_ascii=False)


def main() -> None:
    if SECRETS_PATH.exists():
        raise SystemExit(
            f"O arquivo {SECRETS_PATH} já existe. Edite-o manualmente para não sobrescrever seus secrets."
        )

    email = input("E-mail autorizado: ").strip().casefold()
    name = input("Nome: ").strip() or email
    password = getpass("Senha: ")
    confirmation = getpass("Confirme a senha: ")
    if "@" not in email:
        raise SystemExit("Informe um e-mail válido.")
    if len(password) < 12:
        raise SystemExit("Use uma senha com pelo menos 12 caracteres.")
    if password != confirmation:
        raise SystemExit("As senhas não coincidem.")

    users_json = json.dumps(
        {email: {"name": name, "password_hash": hash_password(password)}},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    contents = "\n".join(
        [
            '# Arquivo local privado. Não envie para o Git.',
            'APP_AUTH_MODE = "local"',
            f"APP_ALLOWED_EMAILS = {_toml_string(email)}",
            f"APP_USERS_JSON = {_toml_string(users_json)}",
            "",
            'JAM_API_BASE = "https://core.proxy.prod.us-west-2.prod.jam.training.aws.dev"',
            "JAM_TOKEN_REFRESH_ENABLED = false",
            'SQLITE_PATH = "./jam_mapper.db"',
            'EXPORT_PATH = "./exports"',
            "",
        ]
    )
    SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SECRETS_PATH.write_text(contents, encoding="utf-8")
    print(f"Configuração criada em: {SECRETS_PATH}")
    print("Agora execute: streamlit run jam_mapper/web/streamlit_app.py")


if __name__ == "__main__":
    main()
