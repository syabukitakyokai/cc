import shutil
from pathlib import Path

from ..import_service import (
    FileAlreadyImportedError,
    ImportResult,
    import_card_usage_records,
)
from ..importers.base import CardImporter
from ..importers.rakuten import RakutenImporter
from ..settings import INPUT_DIR


def create_importer(
    card_code: str,
) -> CardImporter:
    """
    カードコードに対応するインポーターを生成する。
    """

    importers: dict[str, type[CardImporter]] = {
        "rakuten": RakutenImporter,
    }

    try:
        importer_type = importers[card_code]

    except KeyError as error:
        raise ValueError(
            f"Unsupported card code: {card_code}"
        ) from error

    return importer_type()


def import_csv_file(
    *,
    card_code: str,
    file_path: Path,
    withdrawal_month: str,
) -> ImportResult:
    """
    カード利用明細CSVを取り込む。

    正常終了時は、CSVをrawフォルダから
    importedフォルダへ移動する。
    """

    importer = create_importer(card_code)

    records = importer.read(
        file_path=file_path,
        withdrawal_month=withdrawal_month,
    )

    print(f"Card: {card_code}")
    print(f"File: {file_path}")
    print(f"Withdrawal month: {withdrawal_month}")
    print(f"Parsed records: {len(records)}")

    result = import_card_usage_records(
        card_code=card_code,
        source_file=file_path,
        records=records,
    )

    imported_file = move_to_imported_directory(
        card_code=card_code,
        source_file=file_path,
    )

    print("CSV imported successfully.")
    print(f"Imported: {result.imported_count}")
    print(f"Skipped: {result.skipped_count}")
    print(f"Moved to: {imported_file}")

    return result


def move_to_imported_directory(
    *,
    card_code: str,
    source_file: Path,
) -> Path:
    """
    取込完了ファイルをimportedフォルダへ移動する。
    """

    imported_directory = (
        INPUT_DIR
        / card_code
        / "imported"
    )

    imported_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = (
        imported_directory
        / source_file.name
    )

    if destination.exists():
        raise FileExistsError(
            "The destination file already exists: "
            f"{destination}"
        )

    shutil.move(
        str(source_file),
        str(destination),
    )

    return destination


def main(
    *,
    card_code: str,
    file_path: Path,
    withdrawal_month: str,
) -> int:
    """
    import-csvコマンドのエントリーポイント。
    """

    try:
        import_csv_file(
            card_code=card_code,
            file_path=file_path,
            withdrawal_month=withdrawal_month,
        )

        return 0

    except FileAlreadyImportedError as error:
        print(f"CSV import skipped: {error}")

        return 2

    except Exception as error:
        print(f"CSV import failed: {error}")

        return 1