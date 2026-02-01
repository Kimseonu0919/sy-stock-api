# 사용 가이드 (User Guide)

이 문서는 `sy-stock-api`의 직관적인 **체인 방식(Fluent Interface)** 문법과 다양한 매매 시나리오를 설명합니다.

더 전문적인 사용법(Redis, 멀티 계좌 등)은 아래를 참고하세요.
* [전문적 사용 가이드 (Professional Usage Guide)](professional_usage.md)

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

종목 컨텍스트에서 바로 `.buy()` 또는 `.sell()` 메서드를 호출하여 주문을 전송합니다.

<details>
<summary><strong>🛒 매수 주문 (Buy)</strong></summary>




지정가 매수 주문을 전송합니다.

```python
# 삼성전자 10주를 60,000원에 매수
order = broker.symbol("005930").buy(price=60000, qty=10)

print(f"매수 주문 완료: {order.order_id}")
print(f"주문 내용: {order.symbol} {order.qty}주")

```

</details>

<details>
<summary><strong>📉 매도 주문 (Sell)</strong></summary>




보유한 주식을 지정가로 매도합니다.

```python
# 삼성전자 5주를 62,000원에 매도
order = broker.symbol("005930").sell(price=62000, qty=5)

print(f"매도 주문 완료: {order.order_id}")

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