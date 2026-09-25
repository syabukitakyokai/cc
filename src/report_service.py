from .database import fetch_all


def get_monthly_bank_summary(
    withdrawal_month: str,
):
    return fetch_all(
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