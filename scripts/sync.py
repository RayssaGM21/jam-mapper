"""Compatibility wrapper: delegated to package CLI (jam_mapper.cli.sync_cli)."""
from importlib import import_module
import sys
from pathlib import Path


def main():
    # Ensure project root is on sys.path so imports like `jam_mapper` resolve
    script_dir = Path(__file__).resolve().parent
    project_root = str(script_dir.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    mod = import_module("jam_mapper.cli.sync_cli")
    # call click-based main (it will parse sys.argv)
    mod.main()


if __name__ == "__main__":
    main()
