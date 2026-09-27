import csv
from pathlib import Path

from ..models.card_usage_record import (
    CardUsageRecord,
)

from .csv_base import CsvImporterBase


class ViewImporter(
    CsvImporterBase,
):
    """
    Viewカード(JRE CARD)利用明細CSVを読み込む。
    """

    REQUIRED_COLUMNS = (
        "ご利用年月日",
        "ご利用箇所",
        "ご利用額",
        "支払区分（回数）",
    )

    PAYMENT_DATE_LABEL = "お支払日"

    HEADER_FIRST_COLUMN = "ご利用年月日"

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

        with open(
            file_path,
            mode="r",
            encoding=encoding,
            newline="",
        ) as file:

            reader = csv.reader(
                file
            )

            payment_date = ""
            header = None
            header_row_number = 0

            for row_number, row in enumerate(
                reader,
                start=1,
            ):

                if self.is_empty_row(row):
                    continue

                #
                # お支払日
                #
                if (
                    self.get_value(row, 0)
                    == self.PAYMENT_DATE_LABEL
                ):
                    payment_date = (
                        self.get_value(
                            row,
                            1,
                        )
                    )

                #
                # 明細ヘッダ
                #
                if (
                    self.get_value(row, 0)
                    == self.HEADER_FIRST_COLUMN
                ):
                    header = row
                    header_row_number = row_number

                    # 会員行をスキップ
                    next(reader, None)

                    break

            if header is None:
                raise ValueError(
                    "Column header was not found."
                )

            column_indexes = (
                self.create_column_indexes(
                    header,
                    self.REQUIRED_COLUMNS,
                )
            )

            records: list[
                CardUsageRecord
            ] = []

            for row_number, row in enumerate(
                reader,
                start=header_row_number + 1,
            ):

                if self.is_empty_row(row):
                    continue

                usage_date_text = (
                    self.get_column_value(
                        row,
                        column_indexes,
                        "ご利用年月日",
                    )
                )

                if not usage_date_text:
                    continue

                merchant_name = (
                    self.get_column_value(
                        row,
                        column_indexes,
                        "ご利用箇所",
                    )
                )

                amount_text = (
                    self.get_column_value(
                        row,
                        column_indexes,
                        "ご利用額",
                    )
                )

                payment_method = (
                    self.get_column_value(
                        row,
                        column_indexes,
                        "支払区分（回数）",
                    )
                )

                usage_date = (
                    self.parse_date(
                        usage_date_text,
                        formats=(
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
                            f"お支払日: "
                            f"{payment_date}"
                            if payment_date
                            else None
                        ),
                        (
                            f"支払区分: "
                            f"{payment_method}"
                            if payment_method
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