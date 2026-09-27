import csv

from datetime import datetime
from pathlib import Path

from ..models.card_usage_record import (
    CardUsageRecord,
)

from .base import CardImporter


class EposImporter(
    CardImporter,
):

    ENCODING = "cp932"

    HEADER_ROW_INDEX = 1

    def read(
        self,
        file_path: Path,
    ) -> list:
        self._validate_file(
            file_path
        )

        records: list[
            CardUsageRecord
        ] = []

        with open(
            file_path,
            mode="r",
            encoding=self.ENCODING,
            newline="",
        ) as file:

            reader = csv.reader(
                file
            )

            #
            # 1行目
            # 「月別ご利用明細 ～」
            #
            next(reader)

            #
            # 2行目
            # 列ヘッダ
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
                    row[1].strip()
                )

                if not usage_date_text:
                    continue

                usage_date = (
                    self._parse_usage_date(
                        usage_date_text
                    )
                )

                merchant_name = (
                    row[2].strip()
                )

                amount = (
                    self._parse_amount(
                        row[4]
                    )
                )

                #
                # 「お支払開始月」
                #
                payment_start_month = (
                    row[6].strip()
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
    def _validate_file(
        file_path: Path,
    ) -> None:

        if not file_path.is_file():

            raise FileNotFoundError(
                f"CSV file not found: "
                f"{file_path}"
            )

    @staticmethod
    def _parse_usage_date(
        value: str,
    ):

        try:

            return datetime.strptime(
                value,
                "%Y年%m月%d日",
            ).date()

        except ValueError as error:

            raise ValueError(
                f"Invalid usage date: "
                f"{value}"
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

            return int(
                normalized_value
            )

        except ValueError as error:

            raise ValueError(
                f"Invalid amount: "
                f"{value}"
            ) from error

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