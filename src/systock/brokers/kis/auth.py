import requests
import json
import logging
from typing import Optional, Dict

# [수정] utils에서 RateLimiter 가져오기
from ...utils import RateLimiter
from ...exceptions import AuthError

class KisAuthMixin:
    """인증 및 기본 HTTP 통신 관리"""

    # URL 상수
    URL_REAL = "https://openapi.koreainvestment.com:9443"
    URL_VIRTUAL = "https://openapivts.koreainvestment.com:29443"

    # [핵심] 토큰 발급용 전역 제한기 (모든 인스턴스 공유)
    # 1초에 1회 발급 제한 (데코레이터 대신 static 변수로 관리)
    _token_limiter = RateLimiter(max_calls=1, period=1.0)

    def __init__(
        self, app_key: str, app_secret: str, acc_no: str, is_real: bool = False
    ):
        self.app_key = app_key
        self.app_secret = app_secret
        self.acc_no_prefix = acc_no[:8]
        self.acc_no_suffix = acc_no[-2:]
        self.is_real = is_real
        self.base_url = self.URL_REAL if is_real else self.URL_VIRTUAL

        self.access_token: Optional[str] = None
        self._session = requests.Session()

        # 로거 초기화
        self.logger = logging.getLogger("systock.kis")

    # [변경] 데코레이터(@RateLimiter) 제거
    def connect(self) -> bool:
        """토큰 발급"""
        
        # [추가] 제한기 대기 (다른 객체가 발급 중이면 기다림)
        KisAuthMixin._token_limiter.wait()

        self.logger.debug("토큰 발급 시도...")
        url = f"{self.base_url}/oauth2/tokenP"
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }

        resp = requests.post(url, json=body)
        if resp.status_code == 200:
            data = resp.json()
            self.access_token = data["access_token"]
            self.logger.info("KIS API 연결 성공 (Token 발급됨)")
            return True
        else:
            raise AuthError(f"인증(토큰발급) 실패: {resp.text}")

    def _get_headers(self, tr_id: str, data: dict = None) -> Dict[str, str]:
        """헤더 생성 (Hash Key 포함)"""
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }
        if data:
            headers["hashkey"] = self._generate_hash(data)
        return headers

    def _generate_hash(self, data: dict) -> str:
        """Hash Key 생성"""
        url = f"{self.base_url}/uapi/hashkey"
        headers = {
            "content-type": "application/json; charset=utf-8",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }
        resp = requests.post(url, headers=headers, data=json.dumps(data))
        return resp.json()["HASH"]