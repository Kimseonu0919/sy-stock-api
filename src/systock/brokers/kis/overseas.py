# src/systock/brokers/kis/overseas.py


class KisOverseasMixin:
    """해외 주식 기능 (미국, 홍콩 등)"""

    def fetch_overseas_price(self, symbol: str, market_code: str = "NAS") -> dict:
        """해외 주식 현재가 (구현 예정)"""
        pass
