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

## 3. 다중 계좌 관리 (Multi-Account Support)

여러 개의 실전 계좌(본인, 가족, 서브 계좌 등)나 모의투자 계좌를 하나의 프로젝트에서 동시에 관리할 수 있습니다. `.env` 파일에 **별칭(Alias)**을 지정하고 코드에서 불러오는 방식입니다.

### 환경 변수 구성 (.env)

변수명 사이에 `_별칭_`을 넣어 구분합니다. (예: `SUB`, `MOM`)

```ini
# 1. [메인] 기본 실전 계좌
KIS_REAL_APP_KEY=main_app_key
KIS_REAL_APP_SECRET=main_secret
KIS_REAL_ACC_NO=11111111-01

# 2. [서브] 별칭: SUB
KIS_REAL_SUB_APP_KEY=sub_app_key
KIS_REAL_SUB_APP_SECRET=sub_secret
KIS_REAL_SUB_ACC_NO=22222222-01

# 3. [가족] 별칭: MOM
KIS_REAL_MOM_APP_KEY=mom_app_key
KIS_REAL_MOM_APP_SECRET=mom_secret
KIS_REAL_MOM_ACC_NO=33333333-01

```

### 코드 예시

`create_broker` 호출 시 `account_name` 파라미터에 별칭을 전달합니다.

```python
# 1. 메인 계좌 연결 (account_name 생략)
broker_main = create_broker("kis", mode="real")

# 2. 서브 계좌 연결 (KIS_REAL_SUB_... 로드)
broker_sub = create_broker("kis", mode="real", account_name="sub")

# 3. 가족 계좌 연결 (KIS_REAL_MOM_... 로드)
broker_mom = create_broker("kis", mode="real", account_name="mom")

print(f"메인 잔고: {broker_main.balance().deposit}")
print(f"서브 잔고: {broker_sub.balance().deposit}")

```

> **참고:** 토큰 저장소는 계좌번호를 기준으로 데이터를 분리하여 저장하므로, 여러 브로커 인스턴스가 동시에 실행되어도 토큰이 꼬이지 않습니다.

---