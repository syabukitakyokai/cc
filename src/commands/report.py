import csv

from pathlib import Path

from ..report_service import (
    get_monthly_bank_summary,
)

from ..settings import Settings
from ..database import Database

def main(
    *,
    settings: Settings,
    database: Database,
    withdrawal_month: str,
    csv_output: bool,
) -> int:
    
    rows = get_monthly_bank_summary(
        database,
        withdrawal_month
    )

    if csv_output:
        export_csv(
            rows,
            Path(settings.output_dir) / f"bank_summary_{withdrawal_month}.csv"
        )
    else:
        print()
        print(
            f"Report Month: {withdrawal_month}"
        )
        print()

        for row in rows:

            print(
                f"■ {row['account_name']}"
            )

            print(
                f"  Card Amount  : "
                f"{row['card_amount']:,}"
            )

            print(
                f"  Fixed Amount : "
                f"{row['fixed_payment_amount']:,}"
            )

            print(
                f"  Total Amount : "
                f"{row['total_amount']:,}"
            )

            print()

    return 0

def export_csv(
    rows,
    output_file: Path,
):

    with open(
        output_file,
        mode="w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            [
                "Bank",
                "Card Amount",
                "Fixed Amount",
                "Total Amount",
            ]
        )

        for row in rows:

            writer.writerow(
                [
                    row["account_name"],
                    row["card_amount"],
                    row["fixed_payment_amount"],
                    row["total_amount"],
                ]
            )