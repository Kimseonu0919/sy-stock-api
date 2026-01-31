import requests
import json
from typing import Optional, Dict, Any
from ...interfaces.broker import Broker
from ...models import Quote, Order
from ...constants import Side

class KisBroker(Broker):
    """
    한국투자증권(KIS) API 구현체
    실전 투자(Real)와 모의 투자(Virtual) 모드를 지원합니다.
    """
    
    # 기본 URL 설정
    URL_REAL = "https://openapi.koreainvestment.com:9443"
    URL_VIRTUAL = "https://openapivts.koreainvestment.com:29443"

    def __init__(self, app_key: str, app_secret: str, acc_no: str, is_real: bool = False):
        self.app_key = app_key
        self.app_secret = app_secret
        # 계좌번호 포맷 처리 (앞 8자리-뒤 2자리)
        self.acc_no_prefix = acc_no[:8]
        self.acc_no_suffix = acc_no[-2:]
        self.is_real = is_real
        self.base_url = self.URL_REAL if is_real else self.URL_VIRTUAL
        
        self.access_token: Optional[str] = None
        self._session = requests.Session()

    def _get_headers(self, tr_id: str, data: dict = None) -> Dict[str, str]:
        """API 공통 헤더 생성 (Hash Key 포함)"""
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P",  # 개인
        }

        # 주문 등 POST 요청 시 Hash Key 필요 (데이터가 있을 경우)
        if data:
            headers["hashkey"] = self._generate_hash(data)
            
        return headers

    def _generate_hash(self, data: dict) -> str:
        """데이터 변조 방지를 위한 Hash Key 생성"""
        url = f"{self.base_url}/uapi/hashkey"
        headers = {
            "content-type": "application/json; charset=utf-8",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        resp = requests.post(url, headers=headers, data=json.dumps(data))
        resp.raise_for_status()
        return resp.json()["HASH"]

    def connect(self) -> bool:
        """토큰 발급을 통한 API 연결 확인"""
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
            return True
        else:
            raise RuntimeError(f"KIS 연결 실패: {resp.text}")

    def fetch_price(self, symbol: str) -> Quote:
        """현재가 조회 (주식현재가 시세)"""
        if not self.access_token:
            self.connect()

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = self._get_headers(tr_id="FHKST01010100")
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol
        }

        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        
        if data['rt_cd'] != '0':
            raise RuntimeError(f"시세 조회 실패: {data['msg1']}")

        output = data['output']
        return Quote(
            symbol=symbol,
            price=int(output['stck_prpr']),      # 현재가
            volume=int(output['acml_vol']),      # 누적 거래량
            change=float(output['prdy_ctrt'])    # 등락률
        )

    def create_order(self, symbol: str, side: Side, price: int, qty: int) -> Order:
        """주문 전송"""
        if not self.access_token:
            self.connect()

        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
        
        # TR_ID 결정 (실전/모의 & 매수/매도 구분)
        # 실전: 매수(TTTC0802U), 매도(TTTC0801U)
        # 모의: 매수(VTTC0802U), 매도(VTTC0801U)
        tr_id = ""
        if self.is_real:
            tr_id = "TTTC0802U" if side == Side.BUY else "TTTC0801U"
        else:
            tr_id = "VTTC0802U" if side == Side.BUY else "VTTC0801U"

        # 00: 지정가, 01: 시장가 (여기선 지정가 고정)
        order_data = {
            "CANO": self.acc_no_prefix,
            "ACNT_PRDT_CD": self.acc_no_suffix,
            "PDNO": symbol,
            "ORD_DVSN": "00",  
            "ORD_QTY": str(qty),
            "ORD_UNPR": str(price)
        }

        headers = self._get_headers(tr_id=tr_id, data=order_data)
        
        resp = requests.post(url, headers=headers, data=json.dumps(order_data))
        resp.raise_for_status()
        data = resp.json()

        if data['rt_cd'] != '0':
            raise RuntimeError(f"주문 실패: {data['msg1']}")

        # 결과 매핑
        return Order(
            order_id=data['output']['ODNO'],  # 주문번호
            symbol=symbol,
            side=side,
            qty=qty,
            price=price,
            executed=False  # 초기 주문은 미체결 상태
        )