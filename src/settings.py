from pathlib import Path

# --------------------------------------------------
# Project
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --------------------------------------------------
# Database
# --------------------------------------------------

DB_DIR = PROJECT_ROOT / "db"

DB_FILE_NAME = "cc.sqlite"

DB_FILE = DB_DIR / DB_FILE_NAME

# --------------------------------------------------
# SQL
# --------------------------------------------------

SQL_DIR = PROJECT_ROOT / "sql"

SCHEMA_FILE = SQL_DIR / "schema.sql"
VIEWS_FILE = SQL_DIR / "views.sql"

SEED_FILE = SQL_DIR / "seed.sql"

SQL_FILES = [
    SCHEMA_FILE,
    VIEWS_FILE,
    SEED_FILE,
]

# --------------------------------------------------
# Input
# --------------------------------------------------

INPUT_DIR = PROJECT_ROOT / "input"

# --------------------------------------------------
# Output
# --------------------------------------------------

OUTPUT_DIR = PROJECT_ROOT / "output"

# --------------------------------------------------
# Logs
# --------------------------------------------------

LOG_DIR = PROJECT_ROOT / "logs"

# --------------------------------------------------
# Runtime
# --------------------------------------------------

FOREIGN_KEYS = True