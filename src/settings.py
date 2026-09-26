from dataclasses import dataclass
from pathlib import Path
import tomllib


# --------------------------------------------------
# Project
# --------------------------------------------------

PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

DEFAULT_CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "config.toml"
)

# --------------------------------------------------
# Models
# --------------------------------------------------

@dataclass(frozen=True, slots=True)
class Settings:
    config_file: Path

    base_dir: Path

    db_file: Path

    input_dir: Path

    output_dir: Path

    log_dir: Path

    schema_file: Path

    views_file: Path

    seed_file: Path

    card_configs: dict


# --------------------------------------------------
# Utils
# --------------------------------------------------

def resolve_path(
    base_dir: Path,
    value: str,
) -> Path:
    """
    相対パスなら base_dir 基準。
    絶対パスならそのまま返す。
    """

    path = Path(value)

    if path.is_absolute():
        return path

    return base_dir / path


# --------------------------------------------------
# Settings Loader
# --------------------------------------------------

def load_settings(
    config_file: Path | None = None,
) -> Settings:

    #
    # configファイル決定
    #

    if config_file is None:

        config_file = DEFAULT_CONFIG_FILE

        #
        # デフォルト設定時
        # PROJECT_ROOT基準
        #
        base_dir = PROJECT_ROOT

    else:

        #
        # 外部設定時
        # config.tomlの親フォルダ基準
        #
        config_file = config_file.resolve()

        base_dir = config_file.parent

    if not config_file.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_file}"
        )

    #
    # TOML読込
    #

    with open(
        config_file,
        "rb",
    ) as file:

        config = tomllib.load(file)

    #
    # SQL
    #

    sql_dir = (
        PROJECT_ROOT
        / "sql"
    )

    return Settings(
        config_file=config_file,

        base_dir=base_dir,

        db_file=resolve_path(
            base_dir,
            config["paths"]["database"],
        ),

        input_dir=resolve_path(
            base_dir,
            config["paths"]["input_dir"],
        ),

        output_dir=resolve_path(
            base_dir,
            config["paths"]["output_dir"],
        ),

        log_dir=resolve_path(
            base_dir,
            config["paths"]["log_dir"],
        ),

        schema_file=sql_dir / "schema.sql",

        views_file=sql_dir / "views.sql",

        seed_file=sql_dir / "seed.sql",

        card_configs=config["cards"],
    )