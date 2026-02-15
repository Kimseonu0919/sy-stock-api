import json
import time
from typing import List
from ...models import Quote, Order, Balance, Holding
from ...constants import Side
from ...exceptions import ApiError

KIS_ORDER_TYPE_MAP = {
    "지정가": "00",
    "시장가": "01",
    "조건부지정가": "02",
    "최유리지정가": "03",
    "최우선지정가": "04",
    "장전시간외": "05",
    "장후시간외": "06",
    "시간외단일가": "07",
    "IOC지정가": "11",
    "FOK지정가": "12",
    "IOC시장가": "13",
    "FOK시장가": "14",
    "IOC최유리": "15",
    "FOK최유리": "16",
    "중간가": "21",
    "스톱지정가": "22",
    "중간가IOC": "23",
    "중간가FOK": "24",
}


class KisDomesticMixin:
    """국내 주식 매매/조회 기능"""

    def _fetch_price(self, symbol: str) -> Quote:
        """(Internal) 현재가 조회 API 호출"""
        if not self.access_token:
            self.connect()

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = self._get_headers(tr_id="FHKST01010100")
        params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol}

        resp = self.request("GET", url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        if data["rt_cd"] != "0":
            raise ApiError(message=data["msg1"], code=data.get("msg_cd"))

        output = data["output"]

        return Quote(
            price=int(output["stck_prpr"]),
            volume=int(output["acml_vol"]),
            change=float(output["prdy_ctrt"]),
        )

    def order(self, symbol: str, side: Side, qty: int, price: int = 0, order_type: str = "지정가") -> Order:
        """주문 전송"""
        dvsn_code = KIS_ORDER_TYPE_MAP.get(order_type, "00")

        self.logger.info(
            f"주문 요청: {side.value} {symbol} {qty}주 @ {price}원 (유형: {order_type}/{dvsn_code})"
        )
        
        if not self.access_token:
            self.connect()

        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"

        if self.is_real:
            tr_id = "TTTC0802U" if side == Side.BUY else "TTTC0801U"
        else:
            tr_id = "VTTC0802U" if side == Side.BUY else "VTTC0801U"

        order_data = {
            "CANO": self.acc_no_prefix,
            "ACNT_PRDT_CD": self.acc_no_suffix,
            "PDNO": symbol,
            "ORD_DVSN": dvsn_code,
            "ORD_QTY": str(qty),
            "ORD_UNPR": str(price),
        }

        headers = self._get_headers(tr_id=tr_id, data=order_data)
        resp = self.request("POST", url, headers=headers, data=json.dumps(order_data))
        resp.raise_for_status()
        data = resp.json()

        if data["rt_cd"] != "0":
            self.logger.error(f"주문 실패: {data['msg1']}")
            raise ApiError(message=data["msg1"], code=data.get("msg_cd"))

        return Order(
            order_id=data["output"]["ODNO"],
            symbol=symbol,
            side=side,
            qty=qty,
            price=price,
            order_type=order_type
        )

    def cancel(self, symbol: str) -> List[str]:
        """
        특정 종목의 미체결 주문을 조회하여 모두 취소합니다.
        (_cancel_one 메서드 로직을 여기에 통합했습니다.)
        """
        self.logger.info(f"[{symbol}] 종목의 미체결 주문 전량 취소 시도...")
        
        # 1. 미체결 내역 조회
        open_orders = self._fetch_open_orders()
        target_orders = [o for o in open_orders if o['pdno'] == symbol]
        
        if not target_orders:
            self.logger.info(f"[{symbol}] 취소할 미체결 주문이 없습니다.")
            return []

        cancelled_ids = []
        
        # 2. 각 주문에 대해 취소 API 호출 (통합됨)
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-rvsecncl"
        tr_id = "TTTC0013U" if self.is_real else "VTTC0013U"

        for order in target_orders:
            orgn_odno = order['odno']
            qty = int(order['psbl_qty'])
            
            try:
                # API 요청 데이터 생성
                order_data = {
                    "CANO": self.acc_no_prefix,
                    "ACNT_PRDT_CD": self.acc_no_suffix,
                    "KRX_FWDG_ORD_ORGNO": "",
                    "ORGN_ODNO": orgn_odno,
                    "ORD_DVSN": "00",
                    "RVSE_CNCL_DVSN_CD": "02",  # 02: 취소
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": "0",
                    "QTY_ALL_ORD_YN": "Y",      # 잔량 전부 취소
                }

                headers = self._get_headers(tr_id=tr_id, data=order_data)
                resp = self.request("POST", url, headers=headers, data=json.dumps(order_data))
                resp.raise_for_status()
                data = resp.json()

                if data["rt_cd"] != "0":
                    raise ApiError(f"취소 실패: {data['msg1']}")

                cancelled_ids.append(orgn_odno)
                self.logger.info(f"주문취소 완료: 원주문번호 {orgn_odno}, 수량 {qty}")
                
                # 연속 호출 시 API 제한 고려 (안전장치)
                time.sleep(0.05) 

            except ApiError as e:
                self.logger.error(f"주문취소 실패 ({orgn_odno}): {e}")

        return cancelled_ids

    def _fetch_open_orders(self) -> List[dict]:
        """(Internal) 주식 정정/취소 가능 주문 조회 (미체결 내역)"""
        if not self.access_token:
            self.connect()

        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl"
        tr_id = "TTTC8036R" if self.is_real else "VTTC8036R"

        orders = []
        ctx_area_fk100 = ""
        ctx_area_nk100 = ""
        
        while True:
            headers = self._get_headers(tr_id=tr_id)
            params = {
                "CANO": self.acc_no_prefix,
                "ACNT_PRDT_CD": self.acc_no_suffix,
                "CTX_AREA_FK100": ctx_area_fk100,
                "CTX_AREA_NK100": ctx_area_nk100,
                "INQR_DVSN_1": "0",
                "INQR_DVSN_2": "0",
            }

            resp = self.request("GET", url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

            if data["rt_cd"] != "0":
                if data["msg_cd"] == "800000": 
                     break
                raise ApiError(f"미체결 조회 실패: {data['msg1']}")

            for item in data.get("output", []):
                orders.append({
                    "odno": item["odno"],
                    "pdno": item["pdno"],
                    "psbl_qty": item["psbl_qty"]
                })

            tr_cont = resp.headers.get("tr_cont", "M")
            if tr_cont in ["N", "D"]:
                ctx_area_fk100 = data.get("ctx_area_fk100", "")
                ctx_area_nk100 = data.get("ctx_area_nk100", "")
                time.sleep(0.1)
            else:
                break
        
        return orders

    def _fetch_balance(self) -> Balance:
        """잔고 조회"""
        if not self.access_token:
            self.connect()

        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        tr_id = "TTTC8434R" if self.is_real else "VTTC8434R"

        holdings = []
        ctx_area_fk100 = ""
        ctx_area_nk100 = ""
        tr_cont = None

        while True:
            headers = self._get_headers(tr_id=tr_id, tr_cont=tr_cont)
            params = {
                "CANO": self.acc_no_prefix,
                "ACNT_PRDT_CD": self.acc_no_suffix,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "00",
                "CTX_AREA_FK100": ctx_area_fk100,
                "CTX_AREA_NK100": ctx_area_nk100,
            }

            resp = self.request("GET", url, headers=headers, params=params)

            if resp.status_code != 200:
                self.logger.error(f"잔고 조회 중 오류 발생: {resp.text}")
                resp.raise_for_status()

            data = resp.json()
            if data["rt_cd"] != "0":
                raise ApiError(f"잔고 조회 실패: {data['msg1']}")

            for item in data["output1"]:
                if int(item["hldg_qty"]) == 0:
                    continue

                holdings.append(
                    Holding(
                        symbol=item["pdno"],
                        name=item["prdt_name"],
                        qty=int(item["hldg_qty"]),
                        profit_rate=float(item["evlu_pfls_rt"]),
                    )
                )

            tr_cont = resp.headers.get("tr_cont", "M")
            if tr_cont in ["N", "D"]:
                ctx_area_fk100 = data.get("ctx_area_fk100", "")
                ctx_area_nk100 = data.get("ctx_area_nk100", "")
                time.sleep(0.1)
            else:
                break

        summary = data["output2"][0]

        return Balance(
            deposit=int(summary["dnca_tot_amt"]),
            total_asset=int(summary["tot_evlu_amt"]),
            holdings=holdings,
        )