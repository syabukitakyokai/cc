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
) -> int:

    rows = get_monthly_bank_summary(
        database,
        withdrawal_month
    )

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