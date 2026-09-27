import csv

from datetime import datetime
from pathlib import Path

from ..models.card_usage_record import (
    CardUsageRecord,
)

from .base import CardImporter


class NicosImporter(
    CardImporter,
):

    ENCODING = "cp932"

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

            reader = csv.DictReader(
                file
            )

            for row_number, row in enumerate(
                reader,
                start=2,
            ):

                merchant_name = (
                    row[
                        "ご利用店名（海外ご利用店名／海外都市名）"
                    ]
                    .strip()
                )

                #
                # 会員名行
                #
                if merchant_name.startswith("【"):
                    continue

                usage_date_text = (
                    row["ご利用日"]
                    .strip()
                )

                if not usage_date_text:
                    continue

                usage_date = (
                    self._parse_usage_date(
                        usage_date_text
                    )
                )

                amount = (
                    self._parse_amount(
                        row["ご利用金額（円）"]
                    )
                )

                payment_date = (
                    row["お支払日"]
                    .strip()
                )

                records.append(
                    CardUsageRecord(
                        usage_date=usage_date,
                        merchant_name=merchant_name,
                        amount=amount,
                        original_row_number=row_number,
                        description=payment_date
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