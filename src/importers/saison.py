import csv
from datetime import datetime
from pathlib import Path
from typing import TextIO

from ..models.card_usage_record import CardUsageRecord
from .base import CardImporter


class SaisonImporter(CardImporter):
    """
    セゾンカードの利用明細CSVを読み込む。
    """

    ENCODINGS = (
        "utf-8-sig",
        "cp932",
    )

    REQUIRED_COLUMNS = (
        "利用日",
        "ご利用店名及び商品名",
        "支払区分名称",
        "利用金額",
        "備考",
    )

    def read(
        self,
        file_path: Path,
    ) -> list:
        self._validate_file(file_path)

        last_error: UnicodeDecodeError | None = None

        for encoding in self.ENCODINGS:
            try:
                with file_path.open(
                    mode="r",
                    encoding=encoding,
                    newline="",
                ) as file:
                    return self._read_file(
                        file=file,
                        file_path=file_path,
                    )

            except UnicodeDecodeError as error:
                last_error = error

        raise ValueError(
            "Unsupported CSV encoding: "
            f"{file_path}"
        ) from last_error

    def _read_file(
        self,
        *,
        file: TextIO,
        file_path: Path,
    ) -> list:
        reader = csv.reader(file)

        try:
            card_row = next(reader)
            payment_date_row = next(reader)
            billing_amount_row = next(reader)
            next(reader)
            header = next(reader)

        except StopIteration as error:
            raise ValueError(
                f"CSV file has insufficient rows: "
                f"{file_path}"
            ) from error

        self._validate_metadata_row(
            row=card_row,
            expected_name="カード名称",
        )

        self._validate_metadata_row(
            row=payment_date_row,
            expected_name="お支払日",
        )

        self._validate_metadata_row(
            row=billing_amount_row,
            expected_name="今回ご請求額",
        )

        payment_date = self._get_metadata_value(
            payment_date_row
        )

        column_indexes = self._create_column_indexes(
            header
        )

        records: list[CardUsageRecord] = []

        for row_number, row in enumerate(
            reader,
            start=5,
        ):
            if self._is_empty_row(row):
                continue

            try:
                record = self._create_record(
                    row=row,
                    row_number=row_number,
                    column_indexes=column_indexes,
                    payment_date=payment_date,
                )

            except ValueError as error:
                raise ValueError(
                    f"Invalid row at line "
                    f"{row_number} in "
                    f"{file_path.name}: {error}"
                ) from error

            records.append(record)

        if not records:
            raise ValueError(
                f"No usage records were found: "
                f"{file_path}"
            )

        return records

    def _create_record(
        self,
        *,
        row: list[str],
        row_number: int,
        column_indexes: dict[str, int],
        payment_date: str,
    ) -> CardUsageRecord:
        usage_date_text = self._get_column_value(
            row,
            column_indexes,
            "利用日",
        )

        merchant_name = self._get_column_value(
            row,
            column_indexes,
            "ご利用店名及び商品名",
        )

        payment_method = self._get_column_value(
            row,
            column_indexes,
            "支払区分名称",
        )

        amount_text = self._get_column_value(
            row,
            column_indexes,
            "利用金額",
        )

        note = self._get_column_value(
            row,
            column_indexes,
            "備考",
        )

        if not usage_date_text:
            raise ValueError(
                "利用日が空です。"
            )

        if not merchant_name:
            raise ValueError(
                "ご利用店名及び商品名が空です。"
            )

        if not amount_text:
            raise ValueError(
                "利用金額が空です。"
            )

        description_parts: list[str] = []

        if payment_date:
            description_parts.append(
                f"お支払日: {payment_date}"
            )

        if payment_method:
            description_parts.append(
                f"支払区分: {payment_method}"
            )

        if note:
            description_parts.append(
                f"備考: {note}"
            )

        description = (
            " / ".join(description_parts)
            if description_parts
            else None
        )

        return CardUsageRecord(
            usage_date=self._parse_usage_date(
                usage_date_text
            ),
            merchant_name=merchant_name,
            amount=self._parse_amount(
                amount_text
            ),
            original_row_number=row_number,
            description=description,
            source_detail_id=None,
        )

    @classmethod
    def _create_column_indexes(
        cls,
        header: list[str],
    ) -> dict[str, int]:
        normalized_header = [
            value.strip()
            for value in header
        ]

        missing_columns = [
            column
            for column in cls.REQUIRED_COLUMNS
            if column not in normalized_header
        ]

        if missing_columns:
            missing = ", ".join(
                missing_columns
            )

            raise ValueError(
                "Required columns are missing: "
                f"{missing}"
            )

        return {
            column: normalized_header.index(
                column
            )
            for column in cls.REQUIRED_COLUMNS
        }

    @staticmethod
    def _parse_usage_date(
        value: str,
    ):
        try:
            return datetime.strptime(
                value,
                "%Y/%m/%d",
            ).date()

        except ValueError as error:
            raise ValueError(
                f"利用日の形式が不正です: {value}"
            ) from error

    @staticmethod
    def _parse_amount(
        value: str,
    ) -> int:
        normalized_value = (
            value
            .replace(",", "")
            .replace("¥", "")
            .replace("￥", "")
            .strip()
        )

        try:
            return int(normalized_value)

        except ValueError as error:
            raise ValueError(
                f"利用金額の形式が不正です: "
                f"{value}"
            ) from error

    @staticmethod
    def _validate_file(
        file_path: Path,
    ) -> None:
        if not file_path.is_file():
            raise FileNotFoundError(
                f"CSV file not found: "
                f"{file_path}"
            )

    @staticmethod
    def _validate_metadata_row(
        *,
        row: list[str],
        expected_name: str,
    ) -> None:
        if not row:
            raise ValueError(
                f"Metadata row is missing: "
                f"{expected_name}"
            )

        actual_name = row[0].strip()

        if actual_name != expected_name:
            raise ValueError(
                "Unexpected metadata row. "
                f"Expected: {expected_name}, "
                f"actual: {actual_name}"
            )

    @staticmethod
    def _get_metadata_value(
        row: list[str],
    ) -> str:
        if len(row) < 2:
            return ""

        return row[1].strip()

    @staticmethod
    def _is_empty_row(
        row: list[str],
    ) -> bool:
        return not row or all(
            not value.strip()
            for value in row
        )

    @staticmethod
    def _get_value(
        row: list[str],
        index: int,
    ) -> str:
        if index >= len(row):
            return ""

        return row[index].strip()

    @classmethod
    def _get_column_value(
        cls,
        row: list[str],
        column_indexes: dict[str, int],
        column_name: str,
    ) -> str:
        return cls._get_value(
            row,
            column_indexes[column_name],
        )