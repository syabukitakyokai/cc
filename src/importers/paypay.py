import csv
from pathlib import Path

from ..models.card_usage_record import (
    CardUsageRecord,
)

from .csv_base import CsvImporterBase


class PayPayImporter(
    CsvImporterBase,
):
    """
    PayPayカード利用明細CSVを読み込む。
    """

    REQUIRED_COLUMNS = (
        "利用日/キャンセル日",
        "利用店名・商品名",
        "支払区分",
        "利用金額",
        "当月お支払日",
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

                usage_date_text = (
                    row[
                        "利用日/キャンセル日"
                    ]
                    .strip()
                )

                #
                # 遅延損害金などの行
                # 本当は登録したいけど、日付をどうするか決めかねている
                #
                if not usage_date_text:
                    continue

                merchant_name = (
                    row[
                        "利用店名・商品名"
                    ]
                    .strip()
                )

                amount_text = (
                    row[
                        "利用金額"
                    ]
                    .strip()
                )

                payment_method = (
                    row[
                        "支払区分"
                    ]
                    .strip()
                )

                payment_date = (
                    row[
                        "当月お支払日"
                    ]
                    .strip()
                )

                usage_date = (
                    self.parse_date(
                        usage_date_text,
                        formats=(
                            "%Y/%m/%d",
                            "%Y/%m/%d",
                        ),
                        field_name="usage date",
                    )
                )

                amount = (
                    self.parse_amount(
                        amount_text
                    )
                )

                description = (
                    self.build_description(
                        (
                            f"支払区分: "
                            f"{payment_method}"
                            if payment_method
                            else None
                        ),
                        (
                            f"お支払日: "
                            f"{payment_date}"
                            if payment_date
                            else None
                        ),
                    )
                )

                records.append(
                    CardUsageRecord(
                        usage_date=usage_date,
                        merchant_name=merchant_name,
                        amount=amount,
                        original_row_number=row_number,
                        description=description,
                        source_detail_id=None,
                    )
                )

        return records