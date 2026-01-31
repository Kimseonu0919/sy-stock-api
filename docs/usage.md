# 사용 가이드 (User Guide)

이 문서는 `sy-stock-api`의 상세 기능과 다양한 매매 시나리오를 설명합니다.

## 1. 초기 설정 (Setup)

### 브로커 생성

보안을 위해 `.env` 파일을 사용하는 것을 권장하지만, 코드에서 직접 주입할 수도 있습니다.
(기본적으로 `mode`를 명시하지 않으면 가상 투자(`virtual`)로 동작하지 않거나 에러가 날 수 있으므로 명시하는 것이 좋습니다.)

```python
from systock import create_broker

# 방법 1: 환경변수(.env) 자동 로드 (권장)
# .env 파일에 APP_KEY, APP_SECRET, ACC_NO 등이 정의되어 있어야 합니다.
broker = create_broker("kis", mode="virtual")  # 실전은 mode="real"

# 방법 2: 직접 주입 (테스트 또는 다중 계좌용)
broker = create_broker(
    "kis",
    mode="virtual",
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET",
    acc_no="12345678-01"
)

```

## 2. 시세 및 잔고 조회

### 현재가 조회 (Current Price)

종목 코드를 입력하여 현재가, 거래량, 등락률 등을 조회합니다.

```python
quote = broker.price("005930")  # 삼성전자

print(f"현재가: {quote.price}원")
print(f"등락률: {quote.change}%")

```

### 잔고 조회 (Balance)

현재 계좌의 예수금과 보유 종목 현황을 조회합니다.

```python
balance = broker.balance()

print(f"총 평가 자산: {balance.total_asset}원")
print(f"주문 가능 금액: {balance.deposit}원")

for stock in balance.holdings:
    print(f"보유: {stock.name} {stock.qty}주 (수익률 {stock.profit_rate}%)")

```

## 3. 매매 시나리오

### 지정가 매수 (Limit Buy)

원하는 가격에 도달했을 때 체결되는 주문입니다.

```python
from systock.constants import Side

order = broker.order(
    symbol="005930",    # 삼성전자
    side=Side.BUY,      # 매수
    price=69000,        # 69,000원
    qty=10              # 10주
)
print(f"매수 주문 접수 완료: {order.order_id}")

```

### 지정가 매도 (Limit Sell)

보유한 주식을 특정 가격에 매도합니다.
*(현재 버전은 지정가 주문만 지원합니다)*

```python
order = broker.order(
    symbol="005930",
    side=Side.SELL,     # 매도
    price=70000,        # 70,000원
    qty=5               # 5주
)
print(f"매도 주문 접수 완료: {order.order_id}")

```

## 4. 에러 처리 (Error Handling)

API 호출 중 발생할 수 있는 예외를 `systock.exceptions` 모듈을 통해 정교하게 처리할 수 있습니다.

```python
from systock.exceptions import ApiError, NetworkError, ConfigError

try:
    # 존재하지 않는 종목 코드로 조회 시도
    broker.price("INVALID_CODE")

except ApiError as e:
    # 증권사 서버에서 에러를 반환한 경우 (예: 종목코드 없음, 장 종료 등)
    print(f"API 오류 발생: {e}") 
    # e.code로 에러 코드(msg_cd) 접근 가능

except NetworkError:
    # 인터넷 연결이 끊겼거나 타임아웃 발생 시
    print("인터넷 연결을 확인해주세요.")

except ConfigError:
    # API Key 누락 등 설정 오류
    print("설정값이 올바르지 않습니다.")

```

---