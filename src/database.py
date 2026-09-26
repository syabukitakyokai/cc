from contextlib import contextmanager
from pathlib import Path
import sqlite3


class Database:

    def __init__(
        self,
        db_file: Path,
    ) -> None:

        self._db_file = db_file

    @property
    def db_file(self) -> Path:
        return self._db_file

    def create_connection(
        self,
    ) -> sqlite3.Connection:

        self._db_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        connection = sqlite3.connect(
            self._db_file
        )

        connection.row_factory = (
            sqlite3.Row
        )

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        return connection

    def execute_script(
        self,
        sql_file: Path,
    ) -> None:

        if not sql_file.exists():
            raise FileNotFoundError(
                f"SQL file not found: {sql_file}"
            )

        sql = sql_file.read_text(
            encoding="utf-8"
        )

        with self.create_connection() as connection:

            connection.executescript(
                sql
            )

            connection.commit()

    def execute(
        self,
        sql: str,
        parameters: tuple = (),
    ) -> None:

        with self.create_connection() as connection:

            connection.execute(
                sql,
                parameters,
            )

            connection.commit()

    def fetch_one(
        self,
        sql: str,
        parameters: tuple = (),
    ) -> sqlite3.Row | None:

        with self.create_connection() as connection:

            cursor = connection.execute(
                sql,
                parameters,
            )

            return cursor.fetchone()

    def fetch_all(
        self,
        sql: str,
        parameters: tuple = (),
    ) -> list[sqlite3.Row]:

        with self.create_connection() as connection:

            cursor = connection.execute(
                sql,
                parameters,
            )

            return list(
                cursor.fetchall()
            )

    @contextmanager
    def transaction(
        self,
    ):

        connection = self.create_connection()

        try:

            connection.execute(
                "BEGIN"
            )

            yield connection

            connection.commit()

        except Exception:

            connection.rollback()

            raise

        finally:

            connection.close()