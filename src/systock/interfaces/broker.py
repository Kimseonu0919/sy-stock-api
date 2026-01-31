from abc import ABC, abstractmethod
from typing import Optional
from ..models import Quote, Order
from ..constants import Side

class Broker(ABC):
    """모든 증권사 구현체가 상속받아야 할 기본 클래스"""

    @abstractmethod
    def connect(self) -> bool:
        """API 연결/로그인 수행"""
        pass

    @abstractmethod
    def fetch_price(self, symbol: str) -> Quote:
        """현재가 조회"""
        pass

    @abstractmethod
    def create_order(self, symbol: str, side: Side, price: int, qty: int) -> Order:
        """주문 전송"""
        pass
    
    # 헬퍼 함수 (간단한 사용성을 위해)
    def buy(self, symbol: str, price: int, qty: int) -> Order:
        return self.create_order(symbol, Side.BUY, price, qty)

    def sell(self, symbol: str, price: int, qty: int) -> Order:
        return self.create_order(symbol, Side.SELL, price, qty)