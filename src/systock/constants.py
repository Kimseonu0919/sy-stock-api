from enum import Enum


class Side(str, Enum):
    """매수/매도 구분"""

    BUY = "buy"
    SELL = "sell"
