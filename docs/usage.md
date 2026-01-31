# 사용 가이드 (User Guide)

이 문서는 sy-stock-api의 상세 기능과 다양한 매매 시나리오를 설명합니다.

## 1. 초기 설정 (Setup)

### 환경 변수 로드
보안을 위해 `.env` 파일을 사용하는 것을 권장하지만, 코드에서 직접 주입할 수도 있습니다.

```python
from systock import create_broker

# 방법 1: 환경변수(.env) 자동 로드 (권장)
broker = create_broker("kis")

# 방법 2: 직접 주입 (테스트용)
broker = create_broker(
    "kis", 
    app_key="...", 
    app_secret="...", 
    acc_no="12345678-01"
)

```

## 2. 매매 시나리오

### 지정가 매수 (Limit Buy)

원하는 가격에 도달했을 때 체결되는 주문입니다.

```python
from systock.constants import Side

order = broker.create_order(
    symbol="005930",    # 삼성전자
    side=Side.BUY,      # 매수
    price=69000,        # 69,000원
    qty=10              # 10주
)
print(f"주문번호: {order.order_id}")

```

### 시장가 매도 (Market Sell)

현재 가격으로 즉시 매도합니다. (가격 `0` 입력 시 시장가로 처리되는 로직 가정)

```python
order = broker.create_order(
    symbol="005930",
    side=Side.SELL,
    price=0,            # 시장가
    qty=5
)

```

## 3. 에러 처리 (Error Handling)

API 호출 중 발생할 수 있는 예외를 처리하는 방법입니다.

```python
from systock.exceptions import ApiError, NetworkError

try:
    broker.fetch_price("INVALID_CODE")
except ApiError as e:
    print(f"API 오류: {e.code} - {e.message}")
except NetworkError:
    print("인터넷 연결을 확인해주세요.")

```
