from ..database import execute_script

from ..settings import SQL_FILES


def main() -> int:
    try:
        for sql_file in SQL_FILES:
            print(f"Executing {sql_file.name}...")
            execute_script(sql_file)

        print("Database initialized successfully.")

        return 0

    except Exception as ex:
        print(f"Failed to initialize database: {ex}")

        return 1


if __name__ == "__main__":
    raise SystemExit(main())