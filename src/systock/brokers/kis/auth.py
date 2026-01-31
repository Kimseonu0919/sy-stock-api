import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

# [수정] 외부 모듈 임포트 (경로 주의)
from ...utils import RateLimiter
from ...exceptions import AuthError
from ...token_store import TokenStore, FileTokenStore


class KisAuthMixin:
    """인증 및 기본 HTTP 통신 관리"""

    # URL 상수
    URL_REAL = "https://openapi.koreainvestment.com:9443"
    URL_VIRTUAL = "https://openapivts.koreainvestment.com:29443"

    # [핵심] 토큰 발급용 전역 제한기 (모든 인스턴스 공유)
    # 1초에 1회 발급 제한 (데코레이터 대신 static 변수로 관리)
    _token_limiter = RateLimiter(max_calls=1, period=1.0)

    def __init__(
        self,
        app_key: str,
        app_secret: str,
        acc_no: str,
        is_real: bool = False,
        token_store: TokenStore = None,
    ):
        self.app_key = app_key
        self.app_secret = app_secret
        self.acc_no_prefix = acc_no[:8]
        self.acc_no_suffix = acc_no[-2:]
        self.is_real = is_real
        self.base_url = self.URL_REAL if is_real else self.URL_VIRTUAL

        # [변경] 저장소 설정 (기본값: 파일 저장소)
        self.token_store = token_store if token_store else FileTokenStore()

        self.access_token: Optional[str] = None
        self._session = requests.Session()
        self.logger = logging.getLogger("systock.kis")

    def connect(self) -> bool:
        """토큰 발급 (캐싱 우선 확인 -> API 호출)"""

        # 1. 저장소에서 토큰 로드 시도
        # (계좌번호 앞 8자리를 키로 사용하여 조회)
        loaded = self.token_store.load(self.acc_no_prefix)

        if loaded:
            token, expired_at = loaded

            # [유효성 검사] 만료 시간 10분 전까지만 재사용 (여유 버퍼)
            if datetime.now() < expired_at - timedelta(minutes=10):
                self.access_token = token
                self.logger.info("캐시된 토큰 사용 (API 호출 생략)")
                return True
            else:
                self.logger.info(
                    "저장된 토큰이 만료되었거나 임박했습니다. 재발급을 진행합니다."
                )

        # 2. 토큰이 없거나 만료된 경우 API 호출 준비
        # 전역 제한기 대기 (다른 객체가 발급 중이면 기다림)
        KisAuthMixin._token_limiter.wait()

        self.logger.debug("토큰 신규 발급 시도 (API 요청)...")
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

            # KIS 응답 예시: "2025-05-30 12:00:00"
            expired_str = data["access_token_token_expired"]

            # 3. 발급받은 토큰을 저장소에 저장
            self.token_store.save(self.access_token, expired_str, self.acc_no_prefix)

            self.logger.info("KIS API 신규 연결 성공 (Token 발급 및 저장됨)")
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
