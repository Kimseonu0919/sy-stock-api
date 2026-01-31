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


@dataclass
class Holding:
    """보유 종목 정보"""

    symbol: str
    name: str  # 종목명
    qty: int  # 보유 수량
    avg_price: float  # 매입 평균가
    total_price: int  # 평가 금액 (현재가 기준)
    profit: int  # 평가 손익
    profit_rate: float  # 수익률(%)


@dataclass
class Balance:
    """계좌 잔고 정보"""

    deposit: int  # 예수금 (주문 가능 금액)
    total_asset: int  # 총 평가 자산 (예수금 + 주식 평가액)
    profit: int  # 총 평가 손익
    profit_rate: float  # 총 수익률(%)
    holdings: list[Holding]  # 보유 종목 리스트
