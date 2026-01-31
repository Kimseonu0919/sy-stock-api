from abc import ABC, abstractmethod
from ..models import Quote, Order, Balance
from ..constants import Side


class Broker(ABC):
    """모든 증권사 구현체가 상속받아야 할 기본 클래스"""

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def price(self, symbol: str) -> Quote:
        pass

    @abstractmethod
    def order(self, symbol: str, side: Side, price: int, qty: int) -> Order:
        """주문 전송 (매수/매도 통합)"""
        pass

    @abstractmethod
    def balance(self) -> Balance:
        """계좌 잔고 및 보유 종목 조회"""
        pass

    # 헬퍼 함수: 내부적으로 self.order 호출
    def buy(self, symbol: str, price: int, qty: int) -> Order:
        return self.order(symbol, Side.BUY, price, qty)

    def sell(self, symbol: str, price: int, qty: int) -> Order:
        return self.order(symbol, Side.SELL, price, qty)
