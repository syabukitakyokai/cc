from ..settings import Settings
from ..database import Database

def main(
    settings: Settings,
    database: Database
) -> int:

    try:

        for sql_file in (
            settings.schema_file,
            settings.views_file,
            settings.seed_file,
        ):

            print(
                f"Executing {sql_file.name}..."
            )

            database.execute_script(
                sql_file
            )

        print(
            "Database initialized successfully."
        )

        return 0

    except Exception as ex:

        print(
            f"Failed to initialize database: {ex}"
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())