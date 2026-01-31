# src/systock/brokers/kis/auth.py
import requests
import json
import logging
from typing import Optional, Dict

class KisAuthMixin:
    """인증 및 기본 HTTP 통신 관리"""
    
    # URL 상수
    URL_REAL = "https://openapi.koreainvestment.com:9443"
    URL_VIRTUAL = "https://openapivts.koreainvestment.com:29443"

    def __init__(self, app_key: str, app_secret: str, acc_no: str, is_real: bool = False):
        self.app_key = app_key
        self.app_secret = app_secret
        self.acc_no_prefix = acc_no[:8]
        self.acc_no_suffix = acc_no[-2:]
        self.is_real = is_real
        self.base_url = self.URL_REAL if is_real else self.URL_VIRTUAL
        
        self.access_token: Optional[str] = None
        self._session = requests.Session()
        
        # 로거는 client.py의 최종 클래스 이름으로 설정되지만 여기서 미리 초기화
        self.logger = logging.getLogger("systock.kis")

    def connect(self) -> bool:
        """토큰 발급"""
        self.logger.debug("토큰 발급 시도...")
        url = f"{self.base_url}/oauth2/tokenP"
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        resp = requests.post(url, json=body)
        if resp.status_code == 200:
            data = resp.json()
            self.access_token = data['access_token']
            self.logger.info("KIS API 연결 성공 (Token 발급됨)")
            return True
        else:
            raise RuntimeError(f"연결 실패: {resp.text}")

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
            "appsecret": self.app_secret
        }
        resp = requests.post(url, headers=headers, data=json.dumps(data))
        return resp.json()["HASH"]