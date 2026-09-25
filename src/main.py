from pathlib import Path
import argparse
from collections.abc import Callable
from html import parser
from typing import TypeAlias

from .commands.init_db import main as init_db
from .commands.import_csv import main as import_csv

VERSION = "0.1.0"

CommandHandler: TypeAlias = Callable[[], int]


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

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        required=True,
    )

    subparsers.add_parser(
        "init-db",
        help="Initialize database tables and views.",
    )

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

    return parser

def get_command_handler(
    command: str,
) -> CommandHandler:
    """
    コマンドに対応する処理を返す。
    """

    handlers: dict[str, CommandHandler] = {
        "init-db": init_db,
    }

    try:
        return handlers[command]

    except KeyError as error:
        raise ValueError(
            f"Unknown command: {command}"
        ) from error


def main() -> int:
    """
    CLIのエントリーポイント。
    """

    parser = create_parser()
    arguments = parser.parse_args()

    try:

        if arguments.command == "import-csv":

            return import_csv(
                card_code=arguments.card,
                file_path=Path(arguments.file),
                withdrawal_month=arguments.month,
            )

        handler = get_command_handler(
            arguments.command
        )

        return handler()

    except Exception as error:
        parser.exit(
            status=1,
            message=f"Command failed: {error}\n",
        )


if __name__ == "__main__":
    raise SystemExit(main())