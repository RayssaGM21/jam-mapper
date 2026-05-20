"""Public package exports.

Imports are kept lazy so database/config tooling can run even when optional
web/API dependencies are not installed in the current Python environment.
"""

__all__ = ["Settings", "get_settings", "JamClient", "Database", "export_to_xlsx"]


def __getattr__(name):
    if name in {"Settings", "get_settings"}:
        from .core.config import Settings, get_settings

        return {"Settings": Settings, "get_settings": get_settings}[name]
    if name == "JamClient":
        from .core.client import JamClient

        return JamClient
    if name == "Database":
        from .core.db import Database

        return Database
    if name == "export_to_xlsx":
        from .core.exporter import export_to_xlsx

        return export_to_xlsx
    raise AttributeError(name)
