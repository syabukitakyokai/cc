from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class CardUsageRecord:
    usage_date: date
    withdrawal_month: str
    merchant_name: str
    amount: int
    original_row_number: int
    description: str | None = None
    source_detail_id: str | None = None