import threading
from typing import Optional

# 인터페이스 및 유틸리티
from ...interfaces.broker import Broker
from ...utils import RateLimiter
from ...contexts import StockContext, AccountContext

# 기능별 Mixin
from .auth import KisAuthMixin
from .domestic import KisDomesticMixin
from .overseas import KisOverseasMixin
from .realtime import KisRealtimeMixin

import requests
from ...exceptions import ConfigError, NetworkError  # [추가]
from ...token_store import TokenStore


class KisBroker(
    KisAuthMixin,  # 1. 인증/세션 관리 (가장 먼저 초기화)
    KisDomesticMixin,  # 2. 국내주식 기능
    KisOverseasMixin,  # 3. 해외주식 기능
    KisRealtimeMixin,  # 4. 실시간 기능
    Broker,  # 5. 공통 인터페이스 (추상 클래스)
):
    """
    한국투자증권(KIS) 통합 Broker 구현체
    - 기능별 Mixin을 상속받아 구현
    - 계좌 단위 API 유량 제한(Rate Limit)을 전역적으로 관리 (Thread-Safe)
    """

    # [핵심] 계좌번호별 RateLimiter를 공유하기 위한 클래스 변수 (저장소)
    # 구조: {'12345678-01': RateLimiter객체, ...}
    _rate_limiters = {}
    _limiters_lock = threading.Lock()  # 동시 접근 제어용 락

    def __init__(
        self,
        app_key: str,
        app_secret: str,
        acc_no: str,
        is_real: bool = False,
        token_store: TokenStore = None,
    ):
        if not app_key or not app_secret or not acc_no:
            raise ConfigError("API Key 또는 계좌번호가 설정되지 않았습니다.")

        # 1. 부모 클래스(KisAuthMixin) 초기화 -> self.session, self.logger 등 생성
        super().__init__(app_key, app_secret, acc_no, is_real, token_store)

        # 2. 유량 제한 설정 (계좌 단위 공유 로직)
        # 실전: 초당 20건 / 모의: 초당 2건
        max_calls = 20 if is_real else 2
        account_key = acc_no  # 계좌번호를 키로 사용

        # [방어 로직]
        # 이미 이 계좌에 할당된 Limiter가 있다면 그것을 쓰고, 없다면 새로 만듭니다.
        # Lock을 사용하여 여러 스레드/객체가 동시에 접근해도 안전합니다.
        with KisBroker._limiters_lock:
            if account_key not in KisBroker._rate_limiters:
                KisBroker._rate_limiters[account_key] = RateLimiter(
                    max_calls=max_calls, period=1.0
                )

            # 내 인스턴스의 limiter로 할당 (참조 복사)
            self.limiter = KisBroker._rate_limiters[account_key]

        self.logger.info(
            f"KIS Broker 생성 완료 ({'실전' if is_real else '모의'}, 계좌: {acc_no})"
        )

    def request(self, method: str, url: str, **kwargs):
        """
        [통합 요청 메서드]
        모든 Mixin에서 requests.get/post 대신 이 메서드를 사용해야 합니다.
        자동으로 유량 제한을 체크하고 대기(Wait)합니다.
        """

        # 1. 호출 가능할 때까지 대기 (다른 객체가 사용 중이면 기다림)
        self.limiter.wait()

        # 2. 실제 API 요청 전송 (KisAuthMixin의 self._session 사용)
        try:
            return self._session.request(method, url, **kwargs)
        except requests.exceptions.RequestException as e:
            # requests 에러를 NetworkError로 감싸서 던짐
            raise NetworkError(f"네트워크 요청 실패: {e}") from e

    def symbol(self, symbol_code: str) -> StockContext:
        """종목 컨텍스트 반환"""
        return StockContext(self, symbol_code)

    @property
    def my(self) -> AccountContext:
        """내 계좌 컨텍스트 반환"""
        # 매번 새로운 Context를 만들어서 리턴할지, 캐싱할지 결정해야 합니다.
        # 여기서는 호출 시점마다 상태를 새로 확인하기 위해 매번 생성하되,
        # AccountContext 내부에서 Lazy Loading을 수행합니다.
        return AccountContext(self)
