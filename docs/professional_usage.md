# 전문적 사용 가이드 (Professional Usage Guide)

이 문서는 `sy-stock-api`를 실전 트레이딩 서버, 멀티 프로세스 환경, 혹은 보안이 중요한 환경에서 운영하기 위한 고급 설정을 설명합니다.

---

## 1. 선택적 설치 (Optional Installation)

이 라이브러리는 가볍게 유지하기 위해 핵심 기능을 제외한 부가 기능(Redis, Keyring 등)은 선택적으로 설치하도록 구성되어 있습니다. 사용 목적에 따라 아래 명령어로 설치하세요.

### 보안 기능 포함 설치 (Keyring 사용 시)

로컬 PC에서 토큰을 운영체제 키체인에 암호화하여 저장하려면 설치합니다.

```bash
pip install -e ".[secure]"

```

### 서버 기능 포함 설치 (Redis 사용 시)

Redis를 이용해 토큰을 관리하려면 설치합니다.

```bash
pip install -e ".[redis]"

```

### 개발자용 설치 (테스트 및 린트)

라이브러리 코드를 수정하거나 테스트를 돌려보려면 설치합니다.

```bash
pip install -e ".[dev]"

```

---

## 2. 토큰 저장소 전략 (Token Caching Strategy)

`sy-stock-api`는 API 호출 횟수를 절약하고 재시작 시 연결 속도를 높이기 위해 토큰 캐싱 시스템을 제공합니다. 환경에 맞는 저장소를 선택(Strategy Pattern)할 수 있습니다.

### 옵션 A: 파일 저장소 (FileTokenStore) - 기본값

별도 설정이 없으면 프로젝트 루트의 `kis_token.json` 파일에 토큰을 평문으로 저장합니다.

* **장점:** 설정 불필요, 디버깅 용이 (파일 열어서 만료시간 확인 가능)
* **단점:** 보안 취약 (파일 유출 시 토큰 노출), 다중 프로세스 동시 쓰기 위험

```python
# 별도 설정 없이 기본 사용
broker = create_broker("kis")

```

### 옵션 B: 보안 저장소 (KeyringTokenStore) - 로컬 PC용

운영체제의 보안 영역(macOS Keychain, Windows Credential Manager)에 토큰을 암호화하여 저장합니다. 파일이 남지 않아 안전합니다.

* **사전 조건:** `pip install -e ".[secure]"` 설치 필요

```python
from systock import create_broker
from systock.token_store import KeyringTokenStore

# service_name은 임의로 지정 (예: 'my_trading_bot')
store = KeyringTokenStore(service_name="systock_bot")
broker = create_broker("kis", token_store=store)

```

### 옵션 C: Redis 저장소 (RedisTokenStore) - 서버/클라우드용

Redis(In-Memory DB)를 사용하여 토큰을 관리합니다. 여러 대의 봇이 토큰을 공유하거나, 도커(Docker) 컨테이너가 재시작되어도 상태를 유지하기에 적합합니다. `TTL` 기능을 사용하여 만료된 토큰을 자동 삭제합니다.

* **사전 조건:** `pip install -e ".[redis]"` 설치 필요

```python
from systock import create_broker
from systock.token_store import RedisTokenStore

# Redis 서버 접속 정보 입력
store = RedisTokenStore(host="localhost", port=6379, db=0)
broker = create_broker("kis", token_store=store)

```

---

## 3. 유량 제한 (Rate Limiting) 및 스레드 안전성

이 라이브러리는 **Thread-Safe**하게 설계되었습니다.

* **API 제한 준수:** 계좌별로 `RateLimiter`가 전역적으로 공유됩니다. `KisBroker` 객체를 여러 개 생성하더라도, 같은 계좌번호를 사용한다면 API 호출 제한(초당 20건 등)을 초과하지 않도록 자동으로 대기(Wait)합니다.
* **동시성:** `Lock`을 사용하여 멀티 스레드 환경에서 안전하게 요청을 처리합니다.