import csv
from pathlib import Path

from ..models.card_usage_record import (
    CardUsageRecord,
)

from .csv_base import CsvImporterBase


class EposImporter(
    CsvImporterBase,
):
    """
    EPOSカード利用明細CSVを読み込む。
    """

    ENCODINGS = (
        "cp932",
    )

    def read(
        self,
        file_path: Path,
    ) -> list:
        self.validate_file(
            file_path
        )

        encoding = self.detect_encoding(
            file_path
        )

        records: list[
            CardUsageRecord
        ] = []

        with open(
            file_path,
            mode="r",
            encoding=encoding,
            newline="",
        ) as file:

            reader = csv.reader(
                file
            )

            #
            # 1行目
            # 月別ご利用明細
            #
            next(reader)

            #
            # 2行目
            # ヘッダ
            #
            next(reader)

            for row_number, row in enumerate(
                reader,
                start=3,
            ):

                if self._is_summary_row(
                    row
                ):
                    continue

                if self._is_note_row(
                    row
                ):
                    continue

                usage_date_text = (
                    self.get_value(
                        row,
                        1,
                    )
                )

                if not usage_date_text:
                    continue

                usage_date = (
                    self.parse_date(
                        usage_date_text,
                        formats=(
                            "%Y年%m月%d日",
                        ),
                        field_name="usage date",
                    )
                )

                merchant_name = (
                    self.get_value(
                        row,
                        2,
                    )
                )

                amount = (
                    self.parse_amount(
                        self.get_value(
                            row,
                            4,
                        )
                    )
                )

                payment_start_month = (
                    self.get_value(
                        row,
                        6,
                    )
                )

                records.append(
                    CardUsageRecord(
                        usage_date=usage_date,
                        merchant_name=merchant_name,
                        amount=amount,
                        original_row_number=row_number,
                        description=payment_start_month
                        or None,
                    )
                )

        return records

    @staticmethod
    def _is_summary_row(
        row: list[str],
    ) -> bool:

        if not row:
            return True

        first_column = (
            row[0].strip()
        )

        return (
            first_column.endswith(
                "合計"
            )
        )

    @staticmethod
    def _is_note_row(
        row: list[str],
    ) -> bool:

        if not row:
            return True

        first_column = (
            row[0].strip()
        )

        return (
            first_column.startswith("（")
            or first_column.startswith("※")
        )