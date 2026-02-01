# src/systock/contexts.py
from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
from .models import Holding, Quote, Balance
from .constants import Side

if TYPE_CHECKING:
    # Broker 인터페이스 타입 힌트용
    from .interfaces.broker import Broker


class StockContext:
    """
    특정 종목에 대한 작업을 수행하는 컨텍스트 객체
    사용 예: broker.symbol("005930").price
    """

    def __init__(self, broker: Broker, symbol: str):
        self._broker = broker
        self._symbol = symbol
        self._quote: Optional[Quote] = None

    def _ensure_loaded(self):
        if self._quote is None:
            self._quote = self._broker._fetch_price(self._symbol)

    @property
    def price(self) -> int:
        self._ensure_loaded()
        return self._quote.price

    @property
    def volume(self) -> int:
        self._ensure_loaded()
        return self._quote.volume

    @property
    def change(self) -> float:
        self._ensure_loaded()
        return self._quote.change

class AccountContext:
    """
    내 계좌 정보를 다루는 컨텍스트 객체
    사용 예: broker.my.deposit
    """

    def __init__(self, broker: Broker):
        self._broker = broker
        self._balance: Optional[Balance] = None

    def _ensure_loaded(self):
        if self._balance is None:
            self._balance = self._broker._fetch_balance()

    @property
    def deposit(self) -> int:
        self._ensure_loaded()
        return self._balance.deposit

    @property
    def total_asset(self) -> int:
        self._ensure_loaded()
        return self._balance.total_asset

    @property
    def holdings(self) -> List[Holding]:
        self._ensure_loaded()
        return self._balance.holdings

    def refresh(self) -> AccountContext:
        self._balance = None
        return self
