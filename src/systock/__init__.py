import os
from dotenv import load_dotenv
from .interfaces.broker import Broker
from .token_store import TokenStore
from .exceptions import ConfigError

load_dotenv()

def create_broker(
    broker_name: str = "kis", 
    mode: str = "virtual", 
    account_name: str = None,  # [추가] 계좌 별칭 (예: 'sub', 'mom')
    token_store: TokenStore = None
) -> Broker:
    """
    브로커 인스턴스 생성 팩토리
    :param account_name: .env에 설정된 계좌 별칭 (None이면 기본값 사용)
    """
    
    mode = mode.lower()
    is_real = (mode == "real")

    if broker_name.lower() == "kis":
        from .brokers.kis.client import KisBroker

        # 1. 기본 접두사 결정 (KIS_REAL 또는 KIS_VIRT)
        prefix = "KIS_REAL" if is_real else "KIS_VIRT"

        # 2. 계좌 별칭이 있다면 접두사에 추가 (예: KIS_REAL_SUB)
        if account_name:
            prefix = f"{prefix}_{account_name.upper()}"

        # 3. 최종 변수명 조합
        key_var = f"{prefix}_APP_KEY"
        secret_var = f"{prefix}_APP_SECRET"
        acc_var = f"{prefix}_ACC_NO"

        # 4. 로드 및 검증
        app_key = os.getenv(key_var)
        app_secret = os.getenv(secret_var)
        acc_no = os.getenv(acc_var)

        if not all([app_key, app_secret, acc_no]):
            raise ConfigError(
                f"[{mode.upper()}/{account_name if account_name else 'MAIN'}] "
                f"필수 환경변수가 누락되었습니다.\n"
                f"찾고 있는 변수명: {key_var}, {acc_var} ...\n"
                f".env 파일을 확인해주세요."
            )

        # 5. 토큰 저장소 관련 (중요!)
        # 계좌번호가 다르면 TokenStore는 알아서 별도의 키로 저장하므로
        # 같은 store 객체를 써도 꼬이지 않습니다.
        
        return KisBroker(
            app_key=app_key, 
            app_secret=app_secret, 
            acc_no=acc_no, 
            is_real=is_real,
            token_store=token_store
        )

    raise ValueError(f"지원하지 않는 증권사입니다: {broker_name}")