from pathlib import Path
import argparse
from collections.abc import Callable
from html import parser
from typing import TypeAlias

from .settings import load_settings
from .database import Database

from .command_dispatcher import (
    dispatch_command,
)

VERSION = "0.1.0"

def create_parser() -> argparse.ArgumentParser:
    """
    CLI引数パーサーを生成する。
    """

    parser = argparse.ArgumentParser(
        prog="cc",
        description=(
            "Aggregate credit card payments "
            "by withdrawal month and bank account."
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    parser.add_argument(
        "--config",
        type=Path,
        help=(
            "Path to config.toml. "
            "If omitted, config/config.toml is used."
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        required=True,
    )

    subparsers.add_parser(
        "init-db",
        help="Initialize database tables and views.",
    )

    #
    import_parser = subparsers.add_parser(
        "import-csv",
        help="Import credit card CSV."
    )

    import_parser.add_argument(
        "--card",
        required=True,
    )

    import_parser.add_argument(
        "--file",
        required=True,
    )

    import_parser.add_argument(
        "--month",
        required=True,
    )

    #
    report_parser = subparsers.add_parser(
        "report",
        help="Show monthly summary report.",
    )

    report_parser.add_argument(
        "--month",
        required=True,
    )

    subparsers.add_parser(
        "import",
        help=(
            "Automatically import all configured "
            "credit card CSV files."
        ),
    )

    return parser



def main() -> int:
    """
    CLIのエントリーポイント。
    """

    parser = create_parser()

    arguments = parser.parse_args()

    try:

        settings = load_settings(
            arguments.config
        )

        database = Database(
            settings.db_file
        )

        return dispatch_command(
            arguments=arguments,
            settings=settings,
            database=database,
        )

    except Exception as error:
        parser.exit(
            status=1,
            message=f"Command failed: {error}\n",
        )

if __name__ == "__main__":
    raise SystemExit(main())