import hashlib
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .database import Database
from .models.card_usage_record import CardUsageRecord


@dataclass(frozen=True, slots=True)
class ImportResult:
    import_file_id: int
    imported_count: int
    skipped_count: int
    already_imported: bool


class FileAlreadyImportedError(Exception):
    """
    同一内容のファイルが正常に取り込まれている場合に発生する。
    """


def import_card_usage_records(
    *,
    database: Database,
    card_code: str,
    source_file: Path,
    records: Sequence[CardUsageRecord],
) -> ImportResult:
    """
    CardUsageRecordをSQLiteへ登録する。

    import_fileとcard_usageは同一トランザクションで登録する。
    途中で失敗した場合、すべてロールバックする。

    Args:
        database:
            登録先データベース。

        card_code:
            credit_card.card_code。

        source_file:
            取込元CSVファイル。

        records:
            登録するカード利用明細。

    Returns:
        取込結果。

    Raises:
        FileNotFoundError:
            取込元ファイルが存在しない場合。

        ValueError:
            明細が空、引落月が複数、
            またはカードが存在しない場合。

        FileAlreadyImportedError:
            同一内容のファイルが取込済みの場合。

        sqlite3.Error:
            データベース処理に失敗した場合。
    """

    _validate_source_file(source_file)

    withdrawal_month = _get_withdrawal_month(
        records
    )

    file_hash = _calculate_file_hash(
        source_file
    )

    with database.transaction() as connection:
        card_id = _get_card_id(
            connection=connection,
            card_code=card_code,
        )

        existing_import = _find_successful_import(
            connection=connection,
            file_hash=file_hash,
        )

        if existing_import is not None:
            raise FileAlreadyImportedError(
                "The file has already been imported: "
                f"{source_file} "
                f"(previous file: "
                f"{existing_import['original_file_name']}, "
                f"imported at: "
                f"{existing_import['imported_at']})"
            )

        import_file_id = _insert_import_file(
            connection=connection,
            card_id=card_id,
            source_file=source_file,
            file_hash=file_hash,
            withdrawal_month=withdrawal_month,
        )

        imported_count = 0
        skipped_count = 0

        for record in records:
            detail_hash = _calculate_detail_hash(
                card_code=card_code,
                record=record,
            )

            inserted = _insert_card_usage(
                connection=connection,
                card_id=card_id,
                import_file_id=import_file_id,
                record=record,
                detail_hash=detail_hash,
            )

            if inserted:
                imported_count += 1
            else:
                skipped_count += 1

        _update_import_success(
            connection=connection,
            import_file_id=import_file_id,
            row_count=len(records),
            imported_count=imported_count,
            skipped_count=skipped_count,
        )

    return ImportResult(
        import_file_id=import_file_id,
        imported_count=imported_count,
        skipped_count=skipped_count,
        already_imported=False,
    )


def _validate_source_file(
    source_file: Path,
) -> None:
    if not source_file.is_file():
        raise FileNotFoundError(
            f"CSV file not found: {source_file}"
        )


def _get_withdrawal_month(
    records: Sequence[CardUsageRecord],
) -> str:
    if not records:
        raise ValueError(
            "No card usage records were provided."
        )

    withdrawal_months = {
        record.withdrawal_month
        for record in records
    }

    if len(withdrawal_months) != 1:
        values = ", ".join(
            sorted(withdrawal_months)
        )

        raise ValueError(
            "Multiple withdrawal months were found: "
            f"{values}"
        )

    return next(iter(withdrawal_months))


def _calculate_file_hash(
    source_file: Path,
) -> str:
    """
    ファイル内容のSHA-256ハッシュを生成する。
    """

    digest = hashlib.sha256()

    with source_file.open(
        mode="rb"
    ) as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def _calculate_detail_hash(
    *,
    card_code: str,
    record: CardUsageRecord,
) -> str:
    """
    明細の重複判定用SHA-256ハッシュを生成する。

    source_detail_idが存在する場合は優先して使用する。
    存在しない場合は元CSV行番号を含める。

    行番号を含めることで、同一日・同一店舗・同一金額の
    正当な複数明細が重複扱いされるのを防ぐ。
    """

    if record.source_detail_id:
        source = "|".join(
            [
                card_code,
                record.withdrawal_month,
                record.source_detail_id,
            ]
        )

    else:
        source = "|".join(
            [
                card_code,
                record.withdrawal_month,
                record.usage_date.isoformat(),
                record.merchant_name.strip(),
                str(record.amount),
                str(record.original_row_number),
            ]
        )

    return hashlib.sha256(
        source.encode("utf-8")
    ).hexdigest()


def _get_card_id(
    *,
    connection: sqlite3.Connection,
    card_code: str,
) -> int:
    row = connection.execute(
        """
        SELECT id
        FROM credit_card
        WHERE card_code = ?
        """,
        (card_code,),
    ).fetchone()

    if row is None:
        raise ValueError(
            "Enabled credit card was not found: "
            f"{card_code}"
        )

    return int(row["id"])


def _find_successful_import(
    *,
    connection: sqlite3.Connection,
    file_hash: str,
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT
            id,
            original_file_name,
            imported_at
        FROM import_file
        WHERE file_hash = ?
          AND status = 'success'
        """,
        (file_hash,),
    ).fetchone()


def _insert_import_file(
    *,
    connection: sqlite3.Connection,
    card_id: int,
    source_file: Path,
    file_hash: str,
    withdrawal_month: str,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO import_file (
            card_id,
            original_file_name,
            relative_path,
            file_hash,
            withdrawal_month,
            status,
            row_count,
            imported_count,
            skipped_count,
            error_message
        )
        VALUES (
            ?,
            ?,
            ?,
            ?,
            ?,
            'processing',
            0,
            0,
            0,
            NULL
        )
        """,
        (
            card_id,
            source_file.name,
            source_file.as_posix(),
            file_hash,
            withdrawal_month,
        ),
    )

    if cursor.lastrowid is None:
        raise RuntimeError(
            "Failed to create import history."
        )

    return int(cursor.lastrowid)


def _insert_card_usage(
    *,
    connection: sqlite3.Connection,
    card_id: int,
    import_file_id: int,
    record: CardUsageRecord,
    detail_hash: str,
) -> bool:
    cursor = connection.execute(
        """
        INSERT OR IGNORE INTO card_usage (
            card_id,
            import_file_id,
            usage_date,
            withdrawal_month,
            merchant_name,
            amount,
            description,
            original_row_number,
            source_detail_id,
            detail_hash
        )
        VALUES (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )
        """,
        (
            card_id,
            import_file_id,
            record.usage_date.isoformat(),
            record.withdrawal_month,
            record.merchant_name,
            record.amount,
            record.description,
            record.original_row_number,
            record.source_detail_id,
            detail_hash,
        ),
    )

    return cursor.rowcount == 1


def _update_import_success(
    *,
    connection: sqlite3.Connection,
    import_file_id: int,
    row_count: int,
    imported_count: int,
    skipped_count: int,
) -> None:
    cursor = connection.execute(
        """
        UPDATE import_file
        SET
            status = 'success',
            row_count = ?,
            imported_count = ?,
            skipped_count = ?,
            error_message = NULL,
            imported_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            row_count,
            imported_count,
            skipped_count,
            import_file_id,
        ),
    )

    if cursor.rowcount != 1:
        raise RuntimeError(
            "Failed to update import history: "
            f"{import_file_id}"
        )