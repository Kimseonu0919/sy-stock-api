from dataclasses import dataclass
from .constants import Side


@dataclass
class Quote:
    """호가/현재가 정보 (symbol 제거됨)"""

    price: int
    volume: int
    change: float  # 등락률


@dataclass
class Order:
    """주문 결과"""
    order_id: str
    symbol: str
    side: Side
    qty: int
    price: int
    order_type: str


@dataclass
class Holding:
    """보유 종목 정보"""

    symbol: str  # 리스트 내 식별을 위해 유지 필요
    name: str
    qty: int
    profit_rate: float


@dataclass
class Balance:
    """계좌 잔고 정보"""

    deposit: int
    total_asset: int
    holdings: list[Holding]
