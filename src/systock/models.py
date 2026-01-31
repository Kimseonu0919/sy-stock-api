from dataclasses import dataclass
from .constants import Side

@dataclass
class Quote:
    """호가/현재가 정보"""
    symbol: str
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
    executed: bool = False