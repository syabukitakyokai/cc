import csv
from pathlib import Path

from ..models.card_usage_record import (
    CardUsageRecord,
)

from .csv_base import CsvImporterBase


class NicosImporter(
    CsvImporterBase,
):
    """
    NICOS利用明細CSVを読み込む。
    """

    REQUIRED_COLUMNS = (
        "お支払日",
        "ご利用店名（海外ご利用店名／海外都市名）",
        "ご利用日",
        "ご利用金額（円）",
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

            reader = csv.DictReader(
                file
            )

            #
            # DictReader のヘッダ確認
            #
            header = (
                reader.fieldnames
                or []
            )

            self.create_column_indexes(
                header,
                self.REQUIRED_COLUMNS,
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
                if merchant_name.startswith(
                    "【"
                ):
                    continue

                usage_date_text = (
                    row["ご利用日"]
                    .strip()
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

                amount = (
                    self.parse_amount(
                        row[
                            "ご利用金額（円）"
                        ]
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
                        description=(
                            payment_date
                            or None
                        ),
                    )
                )

        return records