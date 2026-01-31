from enum import Enum

class Side(str, Enum):
    """매수/매도 구분"""
    BUY = "buy"
    SELL = "sell"

class Market(str, Enum):
    """시장 구분"""
    KOSPI = "kospi"
    KOSDAQ = "kosdaq"