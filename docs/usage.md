네, 방금 구현한 **주문 취소(`cancel`)** 기능과 **주문 유형(`order_type`)** 상세 내용을 반영하여 업데이트된 `usage.md` 문서 내용입니다.

**주요 변경 사항:**

1. **매수/매도 주문 (`.order`)**: `order_type` 파라미터(시장가, 최유리 등) 사용법과 지원되는 유형 목록을 명시했습니다.
2. **주문 취소 (`.cancel`)**: 미체결 주문을 일괄 취소하는 섹션을 **3. 매매 시나리오** 하단에 추가했습니다.

---

# 사용 가이드 (User Guide)

이 문서는 `sy-stock-api`의 직관적인 **체인 방식(Fluent Interface)** 문법과 다양한 매매 시나리오를 설명합니다.

더 전문적인 사용법(Redis, 멀티 계좌 등)은 아래를 참고하세요.

* [전문적 사용 가이드 (Professional Usage Guide)](https://www.google.com/search?q=professional_usage.md)

---

## 1. 초기 설정 (Setup)

브로커 인스턴스를 생성하고 연결하는 단계입니다. `.env` 파일을 통한 보안 설정을 권장합니다.

<details open>
<summary><strong>🔌 브로커 생성 및 연결 (Click to close)</strong></summary>

### 기본 연결 (권장)

`.env` 파일에 `APP_KEY`, `APP_SECRET` 등이 정의되어 있어야 합니다.

```python
from systock import create_broker

# 1. 브로커 생성 (기본: 모의투자)
broker = create_broker("kis", mode="virtual") 

# 2. 연결 (토큰 자동 발급)
broker.connect()

```

### 직접 주입 (테스트용)

환경 변수 없이 코드에 직접 키를 입력할 수도 있습니다.

```python
broker = create_broker(
    "kis",
    mode="virtual",
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET",
    acc_no="12345678-01"
)
broker.connect()

```

</details>

---

## 2. 시세 및 잔고 조회

직관적인 객체 접근 방식을 통해 데이터를 조회합니다.

<details>
<summary><strong>📈 시세 조회 (Market Data)</strong></summary>

`broker.symbol("종목코드")`를 통해 특정 종목의 컨텍스트를 얻은 후, `.price`, `.volume` 등의 속성에 접근하면 API가 자동으로 호출됩니다.

```python
# 삼성전자(005930) 컨텍스트 생성
samsung = broker.symbol("005930")

# 속성 접근 시점에 데이터 로딩 (Lazy Loading)
print(f"현재가: {samsung.price}원")
print(f"거래량: {samsung.volume}주")
print(f"등락률: {samsung.change}%")

```

</details>

<details>
<summary><strong>💰 잔고 및 자산 (My Account)</strong></summary>

`broker.my`를 통해 내 계좌 정보에 접근합니다.

```python
# 내 계좌 컨텍스트
my_account = broker.my

print(f"주문 가능 금액(예수금): {my_account.deposit}원")
print(f"총 평가 자산: {my_account.total_asset}원")

# 보유 종목 리스트 순회
for stock in my_account.holdings:
    print(f"보유: {stock.name} {stock.qty}주 (수익률 {stock.profit_rate}%)")

```

</details>

---

## 3. 매매 시나리오 (Trading)

주문 전송, 주문 유형 설정, 그리고 미체결 주문 취소 기능을 지원합니다.

<details>
<summary><strong>🛒 매수 주문 (Buy)</strong></summary>

`order` 메서드의 `order_type` 파라미터를 통해 다양한 주문 유형을 지정할 수 있습니다.

**지원 주문 유형:**

* `지정가` (기본값), `시장가`
* `최유리지정가`, `최우선지정가`
* `IOC지정가`, `FOK지정가` 등

```python
from systock.constants import Side

# 1. 지정가 매수 (기본값)
# order_type을 생략하면 자동으로 "지정가"로 처리됩니다.
order_limit = broker.order(
    symbol="005930",
    side=Side.BUY,
    price=60000,
    qty=10
)

# 2. 시장가 매수
# 가격(price)은 0으로 설정하거나 생략하고, order_type을 "시장가"로 지정합니다.
order_market = broker.order(
    symbol="005930",
    side=Side.BUY,
    qty=5,
    order_type="시장가"
)

# 3. 최유리 지정가 매수
order_best = broker.order(
    symbol="005930",
    side=Side.BUY,
    qty=5,
    order_type="최유리지정가"
)

print(f"매수 주문 완료: {order_limit.order_id}")

```

</details>

<details>
<summary><strong>📉 매도 주문 (Sell)</strong></summary>

보유한 주식을 매도합니다. 매수와 동일한 옵션을 사용할 수 있습니다.

```python
from systock.constants import Side

# 시장가로 5주 즉시 매도
order = broker.order(
    symbol="005930",
    side=Side.SELL,
    qty=5,
    order_type="시장가"
)

print(f"매도 주문 완료: {order.order_id}")

```

</details>

<details>
<summary><strong>🚫 주문 취소 (Cancel)</strong></summary>

`broker.cancel()` 메서드를 사용하여 특정 종목의 **모든 미체결 주문(매수/매도 포함)**을 일괄 취소합니다.

```python
# 삼성전자(005930)의 미체결 내역을 조회하여 전량 취소
cancelled_list = broker.cancel("005930")

if cancelled_list:
    print(f"취소된 주문번호 목록: {cancelled_list}")
else:
    print("취소할 미체결 주문이 없습니다.")

```

</details>

---

## 4. 에러 처리 (Error Handling)

API 호출 중 발생할 수 있는 예외를 `systock.exceptions` 모듈을 통해 처리합니다.

<details>
<summary><strong>⚠️ 예외 처리 가이드 (Exceptions)</strong></summary>

```python
from systock.exceptions import ApiError, NetworkError, ConfigError

try:
    # 1. 존재하지 않는 종목 코드로 시세 접근
    price = broker.symbol("INVALID_CODE").price

    # 2. 또는 잔고 부족으로 매수 시도
    broker.symbol("005930").buy(price=1000000, qty=100)

except ApiError as e:
    # 증권사 서버에서 거부한 경우 (장 종료, 종목 없음, 잔고 부족 등)
    print(f"API 오류 발생: {e}") 
    # e.code로 에러 코드(msg_cd) 확인 가능

except NetworkError:
    # 인터넷 연결 끊김, 타임아웃
    print("네트워크 연결을 확인해주세요.")

except ConfigError:
    # 설정값 누락
    print("환경 변수 또는 설정값이 올바르지 않습니다.")

```

</details>