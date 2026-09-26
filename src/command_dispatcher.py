from pathlib import Path
from .database import Database
from .settings import Settings

from .commands.import_csv import (
    main as import_csv,
)

from .commands.init_db import (
    main as init_db,
)

from .commands.report import (
    main as report,
)

from .commands.import_all import (
    main as import_all,
)

def dispatch_command(
    arguments,
    settings: Settings,
    database: Database,
) -> int:

    match arguments.command:

        case "init-db":

            return init_db(
                settings=settings,
                database=database,
            )

        case "report":

            return report(
                settings=settings,
                database=database,
                withdrawal_month=arguments.month,
            )

        case "import-csv":

            return import_csv(
                settings=settings,
                database=database,
                card_code=arguments.card,
                file_path=Path(arguments.file),
                withdrawal_month=arguments.month,
            )

        case "import":
            return import_all(
                settings=settings,
                database=database,
            )

        case _:

            raise ValueError(
                f"Unknown command: {arguments.command}"
            )