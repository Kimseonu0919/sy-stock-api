"""
SY-STOCK-API 데모 스크립트
이 파일은 패키지 사용 예시를 보여줍니다.
실행 전 프로젝트 루트에서 'pip install -e .'을 통해 패키지를 설치해야 합니다.
"""

import os
import sys

# 프로젝트 루트를 path에 추가하여 로컬 개발 중에도 import 가능하게 함
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from systock import create_broker
from systock.constants import Side
from systock.models import Quote, Order

# [추가] 우리가 만든 커스텀 예외 클래스 임포트
from systock.exceptions import (
    SyStockError,
    ConfigError,
    NetworkError,
    ApiError,
    AuthError,
)


def main() -> None:
    """메인 실행 함수"""

    # 1. 브로커 객체 생성 (팩토리 패턴 사용)
    print(">>> 브로커 생성 중...")
    try:
        # .env 파일에서 환경변수를 자동으로 로드합니다.
        broker = create_broker(broker_name="kis", mode="virtual")

    except ConfigError as e:
        print(f"❌ [설정 오류] 필수 환경변수(APP_KEY 등)가 누락되었습니다: {e}")
        return
    except Exception as e:
        print(f"❌ [초기화 오류] 알 수 없는 오류: {e}")
        return

    # 2. 연결 수행
    try:
        if broker.connect():
            print("✅ [성공] API 연결 완료 (Access Token 발급됨)")

    except AuthError as e:
        print(f"⛔ [인증 실패] 토큰 발급에 실패했습니다. API Key를 확인하세요: {e}")
        return
    except NetworkError as e:
        print(f"📡 [네트워크 오류] 인터넷 연결을 확인하세요: {e}")
        return

    # 3. 시세 조회 테스트 (삼성전자: 005930)
    symbol = "005930"
    print(f"\n>>> [{symbol}] 시세 조회 시도...")

    try:
        quote: Quote = broker.price(symbol)
        print(f" - 종목: {quote.symbol}")
        print(f" - 현재가: {quote.price:,}원")
        print(f" - 거래량: {quote.volume:,}주")
        print(f" - 등락률: {quote.change}%")

    except ApiError as e:
        print(f"⚠️ [시세 조회 거부] 증권사 에러 (코드: {e.code}): {e}")
    except NetworkError as e:
        print(f"📡 [통신 오류] {e}")

    # 4. 주문 전송 테스트 (모의투자 매수)
    # 주의: 장 운영 시간에만 동작할 수 있습니다.
    price = 60000
    qty = 10
    print(f"\n>>> [{symbol}] 매수 주문 시도 ({price:,}원 / {qty}주)...")

    try:
        order: Order = broker.order(symbol=symbol, side=Side.BUY, price=price, qty=qty)
        print(f"✅ 주문 접수 완료! 주문번호: {order.order_id}")
        print(f"   내용: {order.side} {order.symbol} {order.qty}주 @ {order.price:,}원")

    except ApiError as e:
        # 주문 거부 (장 종료, 잔고 부족 등)는 여기서 잡힙니다.
        print(f"🚫 [주문 거부] {e}")
    except NetworkError as e:
        print(f"📡 [주문 전송 실패] 네트워크 문제로 주문이 나가지 않았습니다: {e}")

    # 5. 잔고 조회 테스트
    print("\n>>> 내 계좌 잔고 확인...")
    try:
        balance = broker.balance()
        print(f" - 예수금: {balance.deposit:,}원")
        print(f" - 총자산: {balance.total_asset:,}원")
        print(f" - 보유종목 수: {len(balance.holdings)}개")

        for stock in balance.holdings:
            print(
                f"   * {stock.name}({stock.symbol}): {stock.qty}주 (수익률 {stock.profit_rate}%)"
            )

    except ApiError as e:
        print(f"⚠️ [잔고 조회 실패] {e}")
    except Exception as e:
        print(f"❌ [기타 오류] {e}")


if __name__ == "__main__":
    main()
