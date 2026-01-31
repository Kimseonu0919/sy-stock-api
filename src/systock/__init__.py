import os
from dotenv import load_dotenv
from .interfaces.broker import Broker
# [추가] 타입 힌팅을 위해 TokenStore 임포트
from .token_store import TokenStore
from .exceptions import ConfigError

load_dotenv()

def create_broker(
    broker_name: str = "kis", 
    mode: str = "virtual", 
    token_store: TokenStore = None  # [추가] 외부에서 저장소를 주입받을 수 있게 함
) -> Broker:
    """
    브로커 인스턴스 생성 팩토리
    :param broker_name: 증권사 명 ('kis')
    :param mode: 'real' (실전) 또는 'virtual' (모의투자)
    :param token_store: (선택) 커스텀 토큰 저장소 (Redis, Keyring 등)
    """

    if broker_name.lower() == "kis":
        from .brokers.kis.client import KisBroker

        # 환경변수 확인
        app_key = os.getenv("KIS_APP_KEY")
        app_secret = os.getenv("KIS_APP_SECRET")
        acc_no = os.getenv("KIS_ACC_NO")

        if not all([app_key, app_secret, acc_no]):
            raise ConfigError(
                "필수 환경변수(KIS_APP_KEY, KIS_APP_SECRET, KIS_ACC_NO)가 설정되지 않았습니다. .env 파일을 확인해주세요."
            )

        is_real = mode.lower() == "real"

        return KisBroker(
            app_key=app_key, 
            app_secret=app_secret, 
            acc_no=acc_no, 
            is_real=is_real,
            token_store=token_store  # [추가] 생성할 때 저장소를 전달
        )

    raise ValueError(f"지원하지 않는 증권사입니다: {broker_name}")