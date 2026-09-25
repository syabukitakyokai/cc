from pathlib import Path
import sqlite3
import sys


def initialize_database() -> None:
    project_root = Path(__file__).resolve().parent.parent

    db_dir = project_root / "db"
    db_dir.mkdir(exist_ok=True)

    db_file = db_dir / "cc.db"
    schema_file = project_root / "sql" / "schema.sql"

    if not schema_file.exists():
        raise FileNotFoundError(
            f"schema.sql not found: {schema_file}"
        )

    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(db_file)

    try:
        # 外部キー制約を有効化
        conn.execute("PRAGMA foreign_keys = ON")

        # schema.sql実行
        conn.executescript(schema_sql)

        conn.commit()

        print("Database initialized successfully.")
        print(f"Database : {db_file}")
        print(f"Schema   : {schema_file}")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def main() -> int:
    try:
        initialize_database()
        return 0

    except Exception as ex:
        print(f"Failed to initialize database: {ex}")
        return 1


if __name__ == "__main__":
    sys.exit(main())