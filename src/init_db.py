from pathlib import Path
import sqlite3
import sys


def initialize_database() -> None:
    project_root = Path(__file__).resolve().parent.parent

    db_dir = project_root / "db"
    db_dir.mkdir(exist_ok=True)

    db_file = db_dir / "cc.sqlite"
    try:
        with sqlite3.connect(db_file) as conn:
            print(f"Database : {db_file}")

            # 外部キー制約を有効化
            conn.execute("PRAGMA foreign_keys = ON")

            sql_dir = project_root / "sql"
            for filename in ["schema.sql", "seed.sql", "views.sql"]:
                file_path = sql_dir / filename
                if not file_path.exists():
                    raise FileNotFoundError(
                        f"{filename} not found: {file_path}"
                    )

                with open(file_path, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                    print(f"Script   : {file_path}")
                    # sql実行
                    conn.executescript(schema_sql)

            conn.commit()
            print("Database initialized successfully.")
    except Exception:
        print(f"Script execution failed.")
        raise

def main() -> int:
    try:
        initialize_database()
        return 0

    except Exception as ex:
        print(f"Failed to initialize database: {ex}")
        return 1


if __name__ == "__main__":
    sys.exit(main())