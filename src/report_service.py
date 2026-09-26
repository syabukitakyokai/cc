from .database import Database


def get_monthly_bank_summary(
    database: Database,
    withdrawal_month: str,
):

    return database.fetch_all(
        """
        SELECT
            withdrawal_month,
            account_name,
            card_amount,
            fixed_payment_amount,
            total_amount
        FROM v_monthly_bank_summary
        WHERE withdrawal_month = ?
        ORDER BY account_name
        """,
        (
            withdrawal_month,
        ),
    )