class SyStockError(Exception):
    """이 라이브러리에서 발생하는 모든 예외의 기본 클래스"""

    pass


class ConfigError(SyStockError):
    """설정 오류 (API Key 누락 등)"""

    pass


class NetworkError(SyStockError):
    """통신 오류 (인터넷 연결 끊김, 타임아웃 등)"""

    pass


class AuthError(SyStockError):
    """인증 실패 (토큰 발급 실패 등)"""

    pass


class ApiError(SyStockError):
    """API 로직 오류 (주문 거부, 시세 조회 실패 등)"""

    def __init__(self, message: str, code: str = None):
        self.code = code  # API 에러 코드 (예: msg1)
        super().__init__(f"[{code}] {message}" if code else message)
