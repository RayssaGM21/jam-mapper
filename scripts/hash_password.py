"""Generate a password hash for APP_USERS_JSON without exposing the password."""

import sys
from getpass import getpass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from jam_mapper.web.auth import hash_password


def main() -> None:
    password = getpass("Senha: ")
    confirmation = getpass("Confirme a senha: ")
    if not password or password != confirmation:
        raise SystemExit("As senhas não coincidem ou estão vazias.")
    print(hash_password(password))


if __name__ == "__main__":
    main()
