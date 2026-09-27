import csv
from pathlib import Path

from ..models.card_usage_record import (
    CardUsageRecord,
)

from .csv_base import CsvImporterBase


class RakutenImporter(
    CsvImporterBase,
):
    """
    楽天カード利用明細CSVを読み込む。

    「■ご利用キャンセルなど」以降の明細は
    返金・取消として負数化する。
    """

    ENCODINGS = (
        "utf-8-sig",
    )

    CANCEL_SECTION_MARKER = (
        "■ご利用キャンセルなど"
    )

    REQUIRED_COLUMNS = (
        "利用日",
        "利用店名・商品名",
        "支払方法",
        "利用金額",
    )

    def read(
        self,
        file_path: Path,
    ) -> list[CardUsageRecord]:
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

            try:

                header = next(reader)

            except StopIteration as error:

                raise ValueError(
                    f"CSV file is empty: "
                    f"{file_path}"
                ) from error

            column_indexes = (
                self.create_column_indexes(
                    header,
                    self.REQUIRED_COLUMNS,
                )
            )

            is_cancel_section = False

            for row_number, row in enumerate(
                reader,
                start=2,
            ):

                if self.is_empty_row(
                    row
                ):
                    continue

                first_value = (
                    self.get_value(
                        row,
                        0,
                    )
                )

                if (
                    first_value
                    == self.CANCEL_SECTION_MARKER
                ):
                    is_cancel_section = True
                    continue

                record = self._create_record(
                    row=row,
                    row_number=row_number,
                    column_indexes=column_indexes,
                    is_cancel=is_cancel_section,
                )

                records.append(
                    record
                )

        return records

    def _create_record(
        self,
        *,
        row: list[str],
        row_number: int,
        column_indexes: dict[str, int],
        is_cancel: bool,
    ) -> CardUsageRecord:

        usage_date_text = (
            self.get_column_value(
                row,
                column_indexes,
                "利用日",
            )
        )

        merchant_name = (
            self.get_column_value(
                row,
                column_indexes,
                "利用店名・商品名",
            )
        )

        payment_method = (
            self.get_column_value(
                row,
                column_indexes,
                "支払方法",
            )
        )

        amount_text = (
            self.get_column_value(
                row,
                column_indexes,
                "利用金額",
            )
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

        if is_cancel:
            amount = -abs(amount)

        description = (
            self.build_description(
                payment_method,
                (
                    "キャンセル・返金"
                    if is_cancel
                    else None
                ),
            )
        )

        return CardUsageRecord(
            usage_date=usage_date,
            merchant_name=merchant_name,
            amount=amount,
            original_row_number=row_number,
            description=description,
            source_detail_id=None,
        )