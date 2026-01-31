from ...interfaces.broker import Broker
from .auth import KisAuthMixin
from .domestic import KisDomesticMixin
from .overseas import KisOverseasMixin
from .realtime import KisRealtimeMixin


class KisBroker(
    KisAuthMixin,  # [1] 인증 구현체 (먼저!)
    KisDomesticMixin,  # [2] 국내주식 구현체 (먼저!)
    KisOverseasMixin,  # [3] 해외주식 구현체
    KisRealtimeMixin,  # [4] 실시간 구현체
    Broker,  # [5] 인터페이스 (맨 뒤로!)
):
    """
    한국투자증권 통합 Broker 클래스.
    Mixin들이 Broker의 추상 메서드를 오버라이딩하여 구현을 완성합니다.
    """

    pass
