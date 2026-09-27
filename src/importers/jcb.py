import csv
from pathlib import Path
from typing import TextIO

from ..models.card_usage_record import CardUsageRecord
from .csv_base import CsvImporterBase


class JcbImporter(CsvImporterBase):
    """
    JCB形式のカード利用明細CSVを読み込むImporter。
    """

    ENCODINGS = (
        "utf-8-sig",
        "cp932",
    )

    PAYMENT_DATE_LABEL = "今回のお支払日"

    HEADER_FIRST_COLUMN = "ご利用者"

    REQUIRED_COLUMNS = (
        "ご利用者",
        "カテゴリ",
        "ご利用日",
        "ご利用先など",
        "ご利用金額(￥)",
        "支払区分",
        "今回回数",
        "訂正サイン",
        "お支払い金額(￥)",
        "国内／海外",
        "摘要",
        "備考",
    )

    def read(
        self,
        file_path: Path,
    ) -> list:
        """
        JCBのCSVファイルを読み込み、
        CardUsageRecordの一覧へ変換する。
        """

        self.validate_file(
            file_path
        )

        encoding = self.detect_encoding(
            file_path
        )

        with file_path.open(
            mode="r",
            encoding=encoding,
            newline="",
        ) as file:
            return self._read_file(
                file=file,
                file_path=file_path,
            )

    def _read_file(
        self,
        *,
        file: TextIO,
        file_path: Path,
    ) -> list:
        reader = csv.reader(file)

        payment_date = ""
        header: list[str] | None = None
        header_row_number = 0

        for row_number, row in enumerate(
            reader,
            start=1,
        ):
            if self.is_empty_row(row):
                continue

            payment_date_candidate = (
                self._find_payment_date(row)
            )

            if payment_date_candidate:
                payment_date = (
                    payment_date_candidate
                )

            if (
                self.get_value(row, 0)
                == self.HEADER_FIRST_COLUMN
            ):
                header = row
                header_row_number = row_number
                break

        if header is None:
            raise ValueError(
                "Column header was not found: "
                f"{file_path}"
            )

        column_indexes = (
            self.create_column_indexes(
                header,
                self.REQUIRED_COLUMNS,
            )
        )

        records: list[CardUsageRecord] = []

        for row_number, row in enumerate(
            reader,
            start=header_row_number + 1,
        ):
            if self.is_empty_row(row):
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

            if record is not None:
                records.append(record)

        if not records:
            raise ValueError(
                "No usage records were found: "
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
    ) -> CardUsageRecord | None:
        usage_date_text = (
            self.get_column_value(
                row,
                column_indexes,
                "ご利用日",
            )
        )

        if not usage_date_text:
            return None

        merchant_name = (
            self.get_column_value(
                row,
                column_indexes,
                "ご利用先など",
            )
        )

        amount_text = (
            self.get_column_value(
                row,
                column_indexes,
                "ご利用金額(￥)",
            )
        )

        payment_method = (
            self.get_column_value(
                row,
                column_indexes,
                "支払区分",
            )
        )

        category = (
            self.get_column_value(
                row,
                column_indexes,
                "カテゴリ",
            )
        )

        domestic_or_overseas = (
            self.get_column_value(
                row,
                column_indexes,
                "国内／海外",
            )
        )

        summary = (
            self.get_column_value(
                row,
                column_indexes,
                "摘要",
            )
        )

        note = (
            self.get_column_value(
                row,
                column_indexes,
                "備考",
            )
        )

        correction_sign = (
            self.get_column_value(
                row,
                column_indexes,
                "訂正サイン",
            )
        )

        if not merchant_name:
            raise ValueError(
                "ご利用先などが空です。"
            )

        if not amount_text:
            raise ValueError(
                "ご利用金額が空です。"
            )

        amount = self.parse_amount(
            amount_text
        )

        if self._is_correction(
            correction_sign
        ):
            amount = -abs(amount)

        description = self.build_description(
            (
                f"お支払日: {payment_date}"
                if payment_date
                else None
            ),
            (
                f"支払区分: {payment_method}"
                if payment_method
                else None
            ),
            (
                f"カテゴリ: {category}"
                if category
                else None
            ),
            (
                f"国内／海外: "
                f"{domestic_or_overseas}"
                if domestic_or_overseas
                else None
            ),
            (
                f"訂正サイン: "
                f"{correction_sign}"
                if correction_sign
                else None
            ),
            (
                f"摘要: {summary}"
                if summary
                else None
            ),
            (
                f"備考: {note}"
                if note
                else None
            ),
        )

        return CardUsageRecord(
            usage_date=self.parse_date(
                usage_date_text,
                formats=(
                    "%Y/%m/%d",
                ),
                field_name="usage date",
            ),
            merchant_name=merchant_name,
            amount=amount,
            original_row_number=row_number,
            description=description,
            source_detail_id=None,
        )

    @classmethod
    def _find_payment_date(
        cls,
        row: list[str],
    ) -> str:
        """
        行内から「今回のお支払日」を探し、
        直後の値を返す。
        """

        normalized_row = [
            value.strip()
            for value in row
        ]

        try:
            label_index = (
                normalized_row.index(
                    cls.PAYMENT_DATE_LABEL
                )
            )

        except ValueError:
            return ""

        value_index = label_index + 1

        return cls.get_value(
            row,
            value_index,
        )

    @staticmethod
    def _is_correction(
        correction_sign: str,
    ) -> bool:
        """
        訂正サインの有無を判定する。

        訂正サインが付いた明細は、
        取消・訂正として負数へ変換する。
        """

        return bool(
            correction_sign.strip()
        )