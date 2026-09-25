import sqlite3

from pathlib import Path

from .settings import DB_FILE


def create_connection(
    db_file: Path = DB_FILE,
) -> sqlite3.Connection:
    """
    SQLite接続生成
    """

    db_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        db_file
    )

    connection.row_factory = sqlite3.Row

    # 外部キー制約を有効化
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def execute_script(
    sql_file: Path,
) -> None:
    """
    SQLスクリプト実行
    """

    if not sql_file.exists():
        raise FileNotFoundError(
            f"SQL file not found: {sql_file}"
        )

    with create_connection() as connection:
        with open(
            sql_file,
            mode="r",
            encoding="utf-8",
        ) as file:

            sql = file.read()

        connection.executescript(sql)

        connection.commit()


def fetch_all(
    sql: str,
    parameters: tuple = (),
) -> list[sqlite3.Row]:
    """
    SELECT複数件
    """

    with create_connection() as connection:

        cursor = connection.execute(
            sql,
            parameters,
        )

        return list(cursor.fetchall())


def fetch_one(
    sql: str,
    parameters: tuple = (),
) -> sqlite3.Row | None:
    """
    SELECT単一件
    """

    with create_connection() as connection:

        cursor = connection.execute(
            sql,
            parameters,
        )

        return cursor.fetchone()


def execute(
    sql: str,
    parameters: tuple = (),
) -> None:
    """
    INSERT / UPDATE / DELETE
    """

    with create_connection() as connection:

        connection.execute(
            sql,
            parameters,
        )

        connection.commit()