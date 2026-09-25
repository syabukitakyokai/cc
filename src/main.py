import argparse
from collections.abc import Callable
from typing import TypeAlias

from .commands.init_db import main as init_db


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