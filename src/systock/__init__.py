import os
from dotenv import load_dotenv
from .interfaces.broker import Broker

load_dotenv()


def create_broker(broker_name: str = "kis", mode: str = "virtual") -> Broker:
    """
    브로커 인스턴스 생성 팩토리
    :param broker_name: 증권사 명 ('kis')
    :param mode: 'real' (실전) 또는 'virtual' (모의투자)
    """

    if broker_name.lower() == "kis":
        from .brokers.kis.client import KisBroker

        # 환경변수 확인
        app_key = os.getenv("KIS_APP_KEY")
        app_secret = os.getenv("KIS_APP_SECRET")
        acc_no = os.getenv("KIS_ACC_NO")

        if not all([app_key, app_secret, acc_no]):
            raise ValueError(
                ".env 파일에 KIS_APP_KEY, KIS_APP_SECRET, KIS_ACC_NO가 설정되지 않았습니다."
            )

        is_real = mode.lower() == "real"

        return KisBroker(
            app_key=app_key, app_secret=app_secret, acc_no=acc_no, is_real=is_real
        )

    raise ValueError(f"지원하지 않는 증권사입니다: {broker_name}")
