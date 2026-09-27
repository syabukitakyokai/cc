import csv
from datetime import datetime
from pathlib import Path

from ..models.card_usage_record import CardUsageRecord
from .base import CardImporter

class VpassImporter(CardImporter):

    ENCODING = "cp932"

    def read(
        self,
        file_path: Path,
    ) -> list[CardUsageRecord]:

        records = []

        with open(
            file_path,
            encoding=self.ENCODING,
            newline="",
        ) as file:

            reader = csv.reader(file)

            # ヘッダ1行読み飛ばし
            next(reader)

            for row_number, row in enumerate(
                reader,
                start=2,
            ):

                usage_date_text = row[0].strip()

                if not usage_date_text:
                    continue

                usage_date = datetime.strptime(
                    usage_date_text,
                    "%Y/%m/%d",
                ).date()

                merchant_name = row[1].strip()

                amount = int(
                    row[2].replace(",", "")
                )

                records.append(
                    CardUsageRecord(
                        usage_date=usage_date,
                        merchant_name=merchant_name,
                        amount=amount,
                        original_row_number=row_number,
                    )
                )

        return records