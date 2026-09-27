from collections.abc import Sequence
from datetime import date
from datetime import datetime
from pathlib import Path

from .base import CardImporter


class CsvImporterBase(CardImporter):
    """
    CSV形式のカード利用明細Importerに共通する処理。
    """

    ENCODINGS: tuple[str, ...] = (
        "utf-8-sig",
        "cp932",
    )

    @staticmethod
    def validate_file(
        file_path: Path,
    ) -> None:
        """
        入力ファイルの存在と拡張子を検証する。
        """

        if not file_path.is_file():
            raise FileNotFoundError(
                f"CSV file not found: {file_path}"
            )

        if file_path.suffix.lower() != ".csv":
            raise ValueError(
                f"File is not a CSV file: {file_path}"
            )

    @classmethod
    def detect_encoding(
        cls,
        file_path: Path,
    ) -> str:
        """
        定義された文字コードを順番に試し、
        読み込み可能な文字コードを返す。
        """

        last_error: UnicodeDecodeError | None = None

        for encoding in cls.ENCODINGS:
            try:
                file_path.read_text(
                    encoding=encoding
                )

                return encoding

            except UnicodeDecodeError as error:
                last_error = error

        raise ValueError(
            f"Unsupported CSV encoding: {file_path}"
        ) from last_error

    @staticmethod
    def parse_date(
        value: str,
        formats: Sequence[str],
        *,
        field_name: str = "date",
    ) -> date:
        """
        複数の日付形式を順番に試してdateへ変換する。
        """

        normalized_value = value.strip()

        for date_format in formats:
            try:
                return datetime.strptime(
                    normalized_value,
                    date_format,
                ).date()

            except ValueError:
                continue

        expected_formats = ", ".join(
            formats
        )

        raise ValueError(
            f"Invalid {field_name}: {value}. "
            f"Expected formats: {expected_formats}"
        )

    @staticmethod
    def parse_amount(
        value: str,
    ) -> int:
        """
        金額文字列を整数へ変換する。

        カンマ、通貨記号、空白、全角マイナスなどを除去・正規化する。
        """

        normalized_value = (
            value
            .replace(",", "")
            .replace("¥", "")
            .replace("￥", "")
            .replace("円", "")
            .replace("－", "-")
            .replace("△", "-")
            .strip()
        )

        if not normalized_value:
            raise ValueError(
                "Amount is empty."
            )

        try:
            return int(normalized_value)

        except ValueError as error:
            raise ValueError(
                f"Invalid amount: {value}"
            ) from error

    @staticmethod
    def is_empty_row(
        row: Sequence[str],
    ) -> bool:
        """
        空行かどうかを判定する。
        """

        return not row or all(
            not value.strip()
            for value in row
        )

    @staticmethod
    def get_value(
        row: Sequence[str],
        index: int,
    ) -> str:
        """
        指定位置の値を安全に取得する。
        """

        if index < 0 or index >= len(row):
            return ""

        return row[index].strip()

    @classmethod
    def get_column_value(
        cls,
        row: Sequence[str],
        column_indexes: dict[str, int],
        column_name: str,
    ) -> str:
        """
        列名に対応する値を安全に取得する。
        """

        try:
            index = column_indexes[
                column_name
            ]

        except KeyError as error:
            raise ValueError(
                f"Column is not defined: "
                f"{column_name}"
            ) from error

        return cls.get_value(
            row,
            index,
        )

    @staticmethod
    def create_column_indexes(
        header: Sequence[str],
        required_columns: Sequence[str],
    ) -> dict[str, int]:
        """
        ヘッダーから列名とインデックスの対応を作る。
        """

        normalized_header = [
            value
            .replace("\ufeff", "")
            .strip()
            for value in header
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in normalized_header
        ]

        if missing_columns:
            missing = ", ".join(
                missing_columns
            )

            actual = ", ".join(
                repr(column)
                for column in normalized_header
            )

            raise ValueError(
                "Required columns are missing: "
                f"{missing}. "
                f"Actual columns: {actual}"
            )

        return {
            column: normalized_header.index(
                column
            )
            for column in required_columns
        }

    @staticmethod
    def build_description(
        *parts: str | None,
    ) -> str | None:
        """
        空でない値を区切り文字で結合する。
        """

        normalized_parts = [
            part.strip()
            for part in parts
            if (
                part is not None
                and part.strip()
            )
        ]

        if not normalized_parts:
            return None

        return " / ".join(
            normalized_parts
        )