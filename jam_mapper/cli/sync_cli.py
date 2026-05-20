import logging
import click
from jam_mapper.core.sync import sync_challenges


@click.command()
@click.option("--no-full", is_flag=True, default=False, help="Skip per-challenge detail fetch")
def main(no_full: bool):
    """Sincroniza desafios do Jam para o banco local e exporta XLSX."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("jam_mapper.cli.sync")
    full = not no_full
    logger.info("Starting sync (full=%s)", full)
    result = sync_challenges(full=full)
    logger.info("Imported %d challenges -> %s", result["imported"], result["xlsx"])
    if result["detailErrors"]:
        logger.warning("Detail fetch errors: %d", len(result["detailErrors"]))


if __name__ == "__main__":
    main()
