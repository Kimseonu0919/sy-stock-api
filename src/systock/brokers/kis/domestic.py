# src/systock/brokers/kis/domestic.py
import json
from ...models import Quote, Order, Balance, Holding
from ...constants import Side
from ...exceptions import ApiError


class KisDomesticMixin:
    """국내 주식 매매/조회 기능"""

    def price(self, symbol: str) -> Quote:
        """현재가 조회 (주식현재가 시세)"""
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
            symbol=symbol,
            price=int(output["stck_prpr"]),  # 현재가
            volume=int(output["acml_vol"]),  # 누적 거래량
            change=float(output["prdy_ctrt"]),  # 등락률
        )

    def order(self, symbol: str, side: Side, price: int, qty: int) -> Order:
        """주문 전송"""
        self.logger.info(f"주문 요청: {side.value} {symbol} {qty}주 @ {price}원")
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
            "ORD_UNPR": str(price),
        }

        headers = self._get_headers(tr_id=tr_id, data=order_data)

        resp = self.request("POST", url, headers=headers, data=json.dumps(order_data))
        resp.raise_for_status()
        data = resp.json()

        if data["rt_cd"] != "0":
            self.logger.error(f"주문 실패: {data['msg1']}")
            raise ApiError(message=data["msg1"], code=data.get("msg_cd"))

        # 결과 매핑
        ord_no = data["output"]["ODNO"]
        self.logger.info(f"주문 접수 성공! 주문번호: {ord_no}")

        return Order(
            order_id=data["output"]["ODNO"],  # 주문번호
            symbol=symbol,
            side=side,
            qty=qty,
            price=price,
            executed=False,  # 초기 주문은 미체결 상태
        )

    def balance(self) -> Balance:
        """잔고 조회 (주식잔고조회)"""
        self.logger.debug("잔고 조회 요청...")
        if not self.access_token:
            self.connect()

        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"

        # TR_ID: 실전(TTTC8434R) / 모의(VTTC8434R)
        tr_id = "TTTC8434R" if self.is_real else "VTTC8434R"

        headers = self._get_headers(tr_id=tr_id)

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
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }

        resp = self.request("GET", url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        if data["rt_cd"] != "0":
            raise ApiError(f"잔고 조회 실패: {data['msg1']}")

        # 1. 보유 종목 파싱
        holdings = []
        for item in data["output1"]:
            # 보유 수량이 0인 경우 제외 (매도 후 잔여 데이터 등)
            if int(item["hldg_qty"]) == 0:
                continue

            holdings.append(
                Holding(
                    symbol=item["pdno"],
                    name=item["prdt_name"],
                    qty=int(item["hldg_qty"]),
                    avg_price=float(item["pchs_avg_pric"]),
                    total_price=int(item["evlu_amt"]),
                    profit=int(item["evlu_pfls_amt"]),
                    profit_rate=float(item["evlu_pfls_rt"]),
                )
            )

        # 2. 계좌 총 자산 파싱 (output2)
        summary = data["output2"][0]
        self.logger.info(f"잔고 조회 완료. 총자산: {summary['tot_evlu_amt']}원")

        return Balance(
            deposit=int(summary["dnca_tot_amt"]),  # 예수금
            total_asset=int(summary["tot_evlu_amt"]),  # 총 평가금액
            profit=int(summary["evlu_pfls_smtl_amt"]),  # 평가손익합계
            profit_rate=0.0,  # API가 총 수익률은 직접 안 주는 경우가 많아 계산 필요할 수 있음 (여기선 0.0 처리 or 직접 계산)
            holdings=holdings,
        )
