from abc import ABC
from abc import abstractmethod
from pathlib import Path

from ..models.card_usage_record import CardUsageRecord


class CardImporter(ABC):
    @abstractmethod
    def read(
        self,
        file_path: Path,
        withdrawal_month: str,
    ) -> list:
        """
        カード会社のCSVを読み込み、
        共通明細形式へ変換する。
        """

        raise NotImplementedError