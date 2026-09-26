import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..database import Database
from ..import_service import (
    FileAlreadyImportedError,
    ImportResult,
    import_card_usage_records,
)
from ..importer_factory import create_importer
from ..settings import Settings


WITHDRAWAL_MONTH_PATTERN = re.compile(
    r"(?P<year>\d{4})"
    r"(?P<month>0[1-9]|1[0-2])"
)


@dataclass(frozen=True, slots=True)
class FileImportResult:
    source_file: Path
    destination_file: Path | None
    import_result: ImportResult | None
    status: str
    message: str | None = None


@dataclass(frozen=True, slots=True)
class BatchImportResult:
    detected_count: int
    imported_count: int
    skipped_count: int
    failed_count: int


def main(
    *,
    settings: Settings,
    database: Database,
) -> int:
    """
    設定された全カードのCSVを自動取込する。
    """

    try:
        result = import_all_csv_files(
            settings=settings,
            database=database,
        )

        print()
        print("CSV batch import completed.")
        print(
            f"Detected files : "
            f"{result.detected_count}"
        )
        print(
            f"Imported files : "
            f"{result.imported_count}"
        )
        print(
            f"Skipped files  : "
            f"{result.skipped_count}"
        )
        print(
            f"Failed files   : "
            f"{result.failed_count}"
        )

        if result.failed_count > 0:
            return 1

        return 0

    except Exception as error:
        print(
            f"CSV batch import failed: {error}"
        )

        return 1


def import_all_csv_files(
    *,
    settings: Settings,
    database: Database,
) -> BatchImportResult:
    """
    config.tomlに定義されたカードを順番に処理する。

    config.tomlのcards配下のキーを、
    フォルダ名およびcard_codeとして使用する。
    """

    settings.input_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    detected_count = 0
    imported_count = 0
    skipped_count = 0
    failed_count = 0

    for card_code, card_config in (
        settings.card_configs.items()
    ):
        if not isinstance(card_config, dict):
            raise ValueError(
                "Card configuration must be "
                f"a table: {card_code}"
            )

        if not _is_card_enabled(
            card_code=card_code,
            card_config=card_config,
        ):
            print(
                f"Skipping disabled card: "
                f"{card_code}"
            )

            continue

        csv_files = find_csv_files(
            input_dir=settings.input_dir,
            card_code=card_code,
        )

        detected_count += len(csv_files)

        if not csv_files:
            print(
                f"No CSV files found: "
                f"{card_code}"
            )

            continue

        for source_file in csv_files:
            result = import_single_csv_file(
                settings=settings,
                database=database,
                card_code=card_code,
                card_config=card_config,
                source_file=source_file,
            )

            match result.status:
                case "imported":
                    imported_count += 1

                case "skipped":
                    skipped_count += 1

                case "failed":
                    failed_count += 1

                case _:
                    raise ValueError(
                        "Unknown import status: "
                        f"{result.status}"
                    )

    return BatchImportResult(
        detected_count=detected_count,
        imported_count=imported_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
    )


def find_csv_files(
    *,
    input_dir: Path,
    card_code: str,
) -> list:
    """
    カード別rawフォルダ直下のCSVを取得する。
    """

    raw_dir = (
        input_dir
        / card_code
        / "raw"
    )

    raw_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not raw_dir.is_dir():
        raise NotADirectoryError(
            f"Raw path is not a directory: "
            f"{raw_dir}"
        )

    return sorted(
        file_path
        for file_path in raw_dir.iterdir()
        if (
            file_path.is_file()
            and file_path.suffix.lower() == ".csv"
        )
    )


def import_single_csv_file(
    *,
    settings: Settings,
    database: Database,
    card_code: str,
    card_config: dict[str, Any],
    source_file: Path,
) -> FileImportResult:
    """
    1件のCSVを解析してDBへ登録する。

    DB登録に成功した場合のみ、
    CSVをimportedフォルダへ移動する。
    """

    importer_name = _get_importer_name(
        card_code=card_code,
        card_config=card_config,
    )

    print()
    print(f"Processing: {source_file}")
    print(f"Card code: {card_code}")
    print(f"Importer: {importer_name}")

    try:
        withdrawal_month = (
            detect_withdrawal_month(
                source_file
            )
        )

        importer = create_importer(
            importer_name
        )

        records = importer.read(
            file_path=source_file,
            withdrawal_month=withdrawal_month,
        )

        print(
            f"Withdrawal month: "
            f"{withdrawal_month}"
        )
        print(
            f"Parsed records: "
            f"{len(records)}"
        )

        import_result = (
            import_card_usage_records(
                database=database,
                card_code=card_code,
                source_file=source_file,
                records=records,
            )
        )

        destination_file = (
            move_to_imported_directory(
                input_dir=settings.input_dir,
                card_code=card_code,
                source_file=source_file,
            )
        )

        print("CSV imported successfully.")
        print(
            f"Imported records: "
            f"{import_result.imported_count}"
        )
        print(
            f"Skipped records: "
            f"{import_result.skipped_count}"
        )
        print(
            f"Moved to: "
            f"{destination_file}"
        )

        return FileImportResult(
            source_file=source_file,
            destination_file=destination_file,
            import_result=import_result,
            status="imported",
        )

    except FileAlreadyImportedError as error:
        print(
            f"CSV import skipped: {error}"
        )

        return FileImportResult(
            source_file=source_file,
            destination_file=None,
            import_result=None,
            status="skipped",
            message=str(error),
        )

    except Exception as error:
        print(
            f"CSV import failed: {error}"
        )

        return FileImportResult(
            source_file=source_file,
            destination_file=None,
            import_result=None,
            status="failed",
            message=str(error),
        )


def detect_withdrawal_month(
    source_file: Path,
) -> str:
    """
    ファイル名からYYYYMMを検出し、
    YYYY-MM形式の引落月を返す。

    対応例:
        202609.csv
        rakuten_202609.csv
        enavi202609(4095).csv
    """

    match = WITHDRAWAL_MONTH_PATTERN.search(
        source_file.stem
    )

    if match is None:
        raise ValueError(
            "Withdrawal month could not be "
            "detected from the file name: "
            f"{source_file.name}"
        )

    year = match.group("year")
    month = match.group("month")

    return f"{year}-{month}"


def move_to_imported_directory(
    *,
    input_dir: Path,
    card_code: str,
    source_file: Path,
) -> Path:
    """
    取込済みCSVを、同じカードフォルダ内の
    importedフォルダへ移動する。
    """

    imported_dir = (
        input_dir
        / card_code
        / "imported"
    )

    imported_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination_file = (
        imported_dir
        / source_file.name
    )

    if destination_file.exists():
        raise FileExistsError(
            "The destination file already exists: "
            f"{destination_file}"
        )

    shutil.move(
        str(source_file),
        str(destination_file),
    )

    return destination_file


def _is_card_enabled(
    *,
    card_code: str,
    card_config: dict[str, Any],
) -> bool:
    enabled = card_config.get(
        "enabled",
        True,
    )

    if not isinstance(enabled, bool):
        raise ValueError(
            "Card configuration value "
            "'enabled' must be a boolean: "
            f"{card_code}"
        )

    return enabled


def _get_importer_name(
    *,
    card_code: str,
    card_config: dict[str, Any],
) -> str:
    importer_name = card_config.get(
        "importer"
    )

    if not isinstance(importer_name, str):
        raise ValueError(
            "Card configuration value "
            "'importer' must be a string: "
            f"{card_code}"
        )

    importer_name = importer_name.strip()

    if not importer_name:
        raise ValueError(
            "Card configuration value "
            "'importer' must not be empty: "
            f"{card_code}"
        )

    return importer_name