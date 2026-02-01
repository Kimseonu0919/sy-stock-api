import json
import time
from ...models import Quote, Order, Balance, Holding
from ...constants import Side
from ...exceptions import ApiError


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

        # [수정] symbol 인자 제거
        return Quote(
            price=int(output["stck_prpr"]),
            volume=int(output["acml_vol"]),
            change=float(output["prdy_ctrt"]),
        )

    def order(self, symbol: str, side: Side, price: int, qty: int) -> Order:
        """주문 전송"""
        self.logger.info(f"주문 요청: {side.value} {symbol} {qty}주 @ {price}원")
        if not self.access_token:
            self.connect()

        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"

        # TR_ID 결정 (실전/모의 & 매수/매도 구분)
        if self.is_real:
            tr_id = "TTTC0802U" if side == Side.BUY else "TTTC0801U"
        else:
            tr_id = "VTTC0802U" if side == Side.BUY else "VTTC0801U"

        order_data = {
            "CANO": self.acc_no_prefix,
            "ACNT_PRDT_CD": self.acc_no_suffix,
            "PDNO": symbol,
            "ORD_DVSN": "00",  # 00: 지정가
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

        # [수정] 모델 필드 변경 반영 (executed 제거)
        return Order(
            order_id=data["output"]["ODNO"],
            symbol=symbol,
            side=side,
            qty=qty,
            price=price,
        )

    def _fetch_balance(self) -> Balance:
        """잔고 조회 (연속 조회 기능 포함)"""
        self.logger.debug("잔고 조회 요청...")
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

            # [수정] 모델 필드 변경 반영 (avg_price, total_price, profit 제거)
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
                self.logger.debug("잔고 다음 페이지 조회 중...")
                time.sleep(0.1)
            else:
                break

        summary = data["output2"][0]

        # [수정] 모델 필드 변경 반영 (profit, profit_rate 제거)
        return Balance(
            deposit=int(summary["dnca_tot_amt"]),
            total_asset=int(summary["tot_evlu_amt"]),
            holdings=holdings,
        )
