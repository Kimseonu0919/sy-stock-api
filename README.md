# sy-stock-api

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**sy-stock-api**는 한국의 다양한 증권사 API(Korea Investment Securities, Kiwoom, etc.)를 단일 인터페이스로 통합 관리하기 위한 Python 라이브러리입니다.

증권사마다 상이한 API 명세와 데이터 포맷을 **표준화된 객체(DTO)와 인터페이스**로 추상화하여, 개발자가 비즈니스 로직(트레이딩 전략)에만 집중할 수 있도록 돕는 것을 목표로 합니다.

---

## 🚀 Key Features

* **Unified Interface**: 모든 증권사(현재 KIS 지원)를 동일한 메서드(`fetch_price`, `create_order`)로 제어합니다.
* **Type Safety**: Dictionary가 아닌 `dataclass` 기반의 DTO(`Quote`, `Order`)를 반환하여 IDE 자동완성과 타입 안정성을 보장합니다.
* **Factory Pattern**: 문자열 파라미터 하나로 브로커 인스턴스를 교체할 수 있어, 유연한 확장성을 제공합니다.
* **Production Ready**: 재시도 로직, 명확한 에러 핸들링, 환경 변수(`.env`) 기반의 보안 관리가 적용되어 있습니다.

---

## 📦 Installation

PyPI를 통해 설치할 수 있습니다. (배포 예정)

```bash
pip install sy-stock-api

```

개발 버전 설치:

```bash
git clone [https://github.com/your-username/sy-stock-api.git](https://github.com/your-username/sy-stock-api.git)
cd sy-stock-api
pip install -e .

```

---

## ⚙️ Configuration

보안을 위해 API Key와 Secret은 코드에 직접 노출하지 않고 환경 변수로 관리합니다.
프로젝트 루트에 `.env` 파일을 생성하고 아래 내용을 입력하세요.

```ini
# .env file example

# 한국투자증권 (Korea Investment Securities)
KIS_APP_KEY=your_app_key_here
KIS_APP_SECRET=your_app_secret_here
KIS_ACC_NO=12345678-01

```

---

## 📖 Usage

### 1. Basic Example

복잡한 인증 과정 없이 단 몇 줄의 코드로 시세 조회 및 주문이 가능합니다.

```python
from systock import create_broker
from systock.constants import Side

# 1. 브로커 인스턴스 생성 (KIS, 모의투자 모드)
broker = create_broker(broker_name="kis", mode="virtual")

# 2. 연결 (Token 자동 발급)
broker.connect()

# 3. 현재가 조회 (삼성전자)
quote = broker.fetch_price("005930")
print(f"현재가: {quote.price}원 / 등락률: {quote.change}%")

# 4. 매수 주문
order = broker.create_order(
    symbol="005930",
    side=Side.BUY,
    price=60000,
    qty=10
)
print(f"주문 접수 완료: {order.order_id}")

```

---

## 🏗 Architecture

이 프로젝트는 유지보수성과 확장성을 위해 **SOLID 원칙**을 기반으로 설계되었습니다.

* **`Broker` (Interface)**: 모든 증권사가 구현해야 할 추상 기본 클래스(ABC)입니다.
* **`KisBroker` (Implementation)**: REST API 통신, 토큰 관리, Hash Key 생성을 담당하는 구현체입니다.
* **`Factory`**: 클라이언트 코드의 수정 없이 브로커 구현체를 교체할 수 있도록 팩토리 패턴을 사용합니다.
* **`DTO` (Models)**: API 응답을 표준화된 데이터 모델(`Quote`, `Order`)로 변환하여 반환합니다.

---

## 📝 Changelog

### v0.1.0 (2023-10-25)

* **Initial Release**: 프로젝트 초기 구성
* **Core**: `Broker` 인터페이스 및 기본 DTO(`Quote`, `Order`, `Side`) 정의
* **Feature**: 한국투자증권(KIS) REST API 구현체 추가
* OAuth 접근 토큰 자동 발급 및 관리
* Hash Key 생성 로직 구현
* 주식 현재가 시세 조회(`fetch_price`)
* 지정가 매수/매도 주문(`create_order`)


* **Infra**: `pyproject.toml` 기반 패키징 설정 및 `.env` 환경 변수 로드 지원

---

## ⚠️ Disclaimer

본 소프트웨어는 개인의 투자 편의를 위해 개발되었으며, **실제 금전적 손실이 발생할 수 있는 금융 거래**에 사용됩니다.
개발자는 본 라이브러리 사용으로 인해 발생하는 어떠한 금전적 손실이나 시스템 오류에 대해서도 책임지지 않습니다. 실전 매매 전 반드시 모의투자 환경에서 충분한 테스트를 거치시기 바랍니다.

---

## 📄 License

이 프로젝트는 **MIT License** 하에 배포됩니다. 자세한 내용은 [LICENSE](https://www.google.com/search?q=LICENSE) 파일을 참고하세요.

---

## 📧 Contact

기능 제안이나 버그 리포트는 이슈 트래커를 이용해 주시기 바랍니다.

* **Author**: Seungyeon Kim
* **Email**: ksy02k@gmail.com
