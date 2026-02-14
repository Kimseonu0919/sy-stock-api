# src/systock/interfaces/broker.py
from __future__ import annotations  # [중요] 타입 힌트 지연 평가 (Python 3.7+)
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

# 런타임에 필요한 공통 모듈 (순환 참조 위험 없음)
from ..models import Order, Quote, Balance
from ..constants import Side

# [TYPE_CHECKING] 런타임에는 실행되지 않고, IDE/TypeChecker에서만 인식
if TYPE_CHECKING:
    from ..contexts import AccountContext, StockContext


class Broker(ABC):
    """모든 증권사 구현체가 상속받아야 할 기본 클래스"""

    @property
    @abstractmethod
    def my(self) -> AccountContext:
        """내 계좌 정보 접근 (AccountContext 반환)"""
        pass

    @abstractmethod
    def symbol(self, symbol_code: str) -> StockContext:
        """특정 종목 접근 (StockContext 반환)"""
        pass

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def order(self, symbol: str, side: Side, qty: int, price: int = 0, order_type: str = "지정가") -> Order:
        """
        주문 전송
        :param order_type: '지정가', '시장가', '최유리지정가' 등 (constants.ORDER_TYPE_MAP 참고)
        """
        pass

    # [내부 구현용 추상 메서드]
    @abstractmethod
    def _fetch_price(self, symbol: str) -> Quote:
        pass

    @abstractmethod
    def _fetch_balance(self) -> Balance:
        pass
