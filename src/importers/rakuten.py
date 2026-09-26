import csv
from datetime import datetime
from pathlib import Path

from ..models.card_usage_record import CardUsageRecord
from .base import CardImporter


class RakutenImporter(CardImporter):
    """
    楽天カードの利用明細CSVを読み込むインポーター。

    「■ご利用キャンセルなど」以降の明細は、
    返金・取消として金額を負数へ変換する。
    """

    ENCODING = "utf-8-sig"

    CANCEL_SECTION_MARKER = "■ご利用キャンセルなど"

    REQUIRED_COLUMNS = (
        "利用日",
        "利用店名・商品名",
        "支払方法",
        "利用金額",
    )

    def read(
        self,
        file_path: Path,
        withdrawal_month: str,
    ) -> list:
        """
        楽天カードCSVを読み込み、共通明細へ変換する。

        Args:
            file_path:
                読み込むCSVファイル。

            withdrawal_month:
                引落月。YYYY-MM形式。

        Returns:
            変換後のカード利用明細。

        Raises:
            FileNotFoundError:
                CSVファイルが存在しない場合。

            ValueError:
                引落月やCSVの内容が不正な場合。
        """

        self._validate_file(file_path)
        self._validate_withdrawal_month(
            withdrawal_month
        )

        records: list[CardUsageRecord] = []

        with file_path.open(
            mode="r",
            encoding=self.ENCODING,
            newline="",
        ) as file:
            reader = csv.reader(file)

            try:
                header = next(reader)

            except StopIteration as error:
                raise ValueError(
                    f"CSV file is empty: {file_path}"
                ) from error

            column_indexes = self._create_column_indexes(
                header
            )

            is_cancel_section = False

            for row_number, row in enumerate(
                reader,
                start=2,
            ):
                if self._is_empty_row(row):
                    continue

                first_value = self._get_value(
                    row,
                    0,
                )

                if first_value == self.CANCEL_SECTION_MARKER:
                    is_cancel_section = True
                    continue

                try:
                    record = self._create_record(
                        row=row,
                        row_number=row_number,
                        column_indexes=column_indexes,
                        withdrawal_month=withdrawal_month,
                        is_cancel=is_cancel_section,
                    )

                except ValueError as error:
                    raise ValueError(
                        f"Invalid row at line "
                        f"{row_number} in {file_path.name}: "
                        f"{error}"
                    ) from error

                records.append(record)

        return records

    def _create_record(
        self,
        row: list[str],
        row_number: int,
        column_indexes: dict[str, int],
        withdrawal_month: str,
        is_cancel: bool,
    ) -> CardUsageRecord:
        usage_date_text = self._get_column_value(
            row,
            column_indexes,
            "利用日",
        )

        merchant_name = self._get_column_value(
            row,
            column_indexes,
            "利用店名・商品名",
        )

        payment_method = self._get_column_value(
            row,
            column_indexes,
            "支払方法",
        )

        amount_text = self._get_column_value(
            row,
            column_indexes,
            "利用金額",
        )

        if not usage_date_text:
            raise ValueError(
                "利用日が空です。"
            )

        if not merchant_name:
            raise ValueError(
                "利用店名・商品名が空です。"
            )

        if not amount_text:
            raise ValueError(
                "利用金額が空です。"
            )

        usage_date = self._parse_usage_date(
            usage_date_text
        )

        amount = self._parse_amount(
            amount_text
        )

        if is_cancel:
            amount = -abs(amount)

        description_parts = []

        if payment_method:
            description_parts.append(
                payment_method
            )

        if is_cancel:
            description_parts.append(
                "キャンセル・返金"
            )

        description = (
            " / ".join(description_parts)
            if description_parts
            else None
        )

        return CardUsageRecord(
            usage_date=usage_date,
            withdrawal_month=withdrawal_month,
            merchant_name=merchant_name,
            amount=amount,
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
                f"Required columns are missing: {missing}"
            )

        return {
            column: normalized_header.index(column)
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
                f"利用金額の形式が不正です: {value}"
            ) from error

    @staticmethod
    def _validate_file(
        file_path: Path,
    ) -> None:
        if not file_path.is_file():
            raise FileNotFoundError(
                f"CSV file not found: {file_path}"
            )

    @staticmethod
    def _validate_withdrawal_month(
        withdrawal_month: str,
    ) -> None:
        try:
            datetime.strptime(
                withdrawal_month,
                "%Y-%m",
            )

        except ValueError as error:
            raise ValueError(
                "withdrawal_month must be "
                f"YYYY-MM format: {withdrawal_month}"
            ) from error

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