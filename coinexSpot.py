# -*- coding: utf-8 -*-
import hashlib
import json
import time
import hmac
from urllib.parse import urlencode
import requests

ACCESS_ID = ""  # Your access id
SECRET_KEY = ""  # Your secret key


class CoinExClient(object):
    BASE_URL = "https://api.coinex.com/v2"
    HEADERS_TEMPLATE = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json"
    }

    def __init__(self, access_id, secret_key):
        self.access_id = access_id
        self.secret_key = secret_key
        self.headers_template = self.HEADERS_TEMPLATE.copy()

    def gen_sign(self, method, request_path, body, timestamp):
        prepared_str = f"{method}{request_path}{body}{timestamp}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            msg=prepared_str.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest().lower()
        return signature

    def get_common_headers(self, signed_str, timestamp):
        headers = self.headers_template.copy()
        headers["X-COINEX-KEY"] = self.access_id
        headers["X-COINEX-SIGN"] = signed_str
        headers["X-COINEX-TIMESTAMP"] = timestamp
        return headers

    def _request(self, method, request_path, params=None, data=None):
        method = method.upper()
        timestamp = str(int(time.time() * 1000))
        params = params or {}
        params = {k: v for k, v in params.items() if v is not None}

        # Build full request path with query parameters
        if params:
            query_string = urlencode(params)
            full_request_path = f"{request_path}?{query_string}"
        else:
            full_request_path = request_path

        url = self.BASE_URL + full_request_path

        # Prepare body for signature (only for POST calls)
        body_for_sign = data if method == "POST" and data else ""
        signed_str = self.gen_sign(method, full_request_path, body_for_sign, timestamp)
        headers = self.get_common_headers(signed_str, timestamp)

        # Make the request
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, data=data, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        # Validate response HTTP status
        if response.status_code != 200:
            raise ValueError(f"Request Error {response.status_code}: {response.text}")

        # Decode the JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON response")

        if response_data.get('code', 0) != 0:
            raise ValueError(f"API Error {response_data.get('code')}: {response_data.get('message', 'No error message')}")

        # Return the parsed JSON data instead of the raw Response object.
        return response_data["data"]

    # API Endpoint Methods
    def account_info(self):
        request_path = "/spot/market"
        return self._request("GET", request_path)
    def get_coin_info(self,ccy=None):
        request_path = "/assets/info"
        if ccy: 
            params={"ccy": ccy}
            return self._request("GET", request_path, params=params)
        else:
            return self._request("GET", request_path)
        
    def get_spot_market(self, market="BTCUSDT"):
        request_path = "/spot/market"
        params = {"market": market}
        return self._request("GET", request_path, params=params)

    def get_spot_balance(self):
        request_path = "/assets/spot/balance"
        return self._request("GET", request_path)

    def get_deposit_address(self, ccy="USDT", chain="CSC"):
        request_path = "/assets/deposit-address"
        params = {"ccy": ccy, "chain": chain}
        return self._request("GET", request_path, params=params)

    def place_order(self, market, market_type, side, order_type, amount, price=None, client_id=None, is_hide=False):
        request_path = "/spot/order"
        data = {
            "market": market,
            "market_type": market_type,
            "side": side,
            "type": order_type,
            "amount": str(amount),
            "is_hide": is_hide
        }
        if client_id is not None:
            data["client_id"] = client_id
        if order_type == "limit":
            if price is None:
                raise ValueError("Limit orders require a price.")
            data["price"] = str(price)
        
        body = json.dumps(data, sort_keys=True)
        return self._request("POST", request_path, data=body)

    def cancel_order(self, market, order_id):
        request_path = "/spot/cancel-order"
        data = {"market": market, "order_id": order_id}
        body = json.dumps(data, sort_keys=True)
        return self._request("POST", request_path, data=body)

    def get_order_details(self, market, order_id):
        request_path = "/spot/order-deals"
        params = {"market": market, "order_id": order_id}
        return self._request("GET", request_path, params=params)

    def get_order_history(self, market, limit=50):
        request_path = "/spot/order/history"
        params = {"market": market, "limit": limit}
        return self._request("GET", request_path, params=params)

    def get_market_ticker(self, market="BTCUSDT"):
        request_path = "/spot/ticker"
        params = {"market": market}
        return self._request("GET", request_path, params=params)

    def get_all_tickers(self):
        request_path = "/spot/allTickers"
        return self._request("GET", request_path)

    def get_market_depth(self, market="BTCUSDT", limit=10):
        request_path = "/spot/depth"
        params = {"market": market, "limit": limit}
        return self._request("GET", request_path, params=params)

    def get_market_kline(self, market="BTCUSDT", kline_type="1min", limit=100):
        request_path = "/spot/kline"
        params = {"market": market, "type": kline_type, "limit": limit}
        return self._request("GET", request_path, params=params)


def run_demo():
    client = CoinExClient(ACCESS_ID, SECRET_KEY)
    # The get_market_ticker method now returns parsed JSON data,
    # allowing a direct, prettier print if needed.
    try:
        response = client.get_market_ticker("BTCUSDT")
        print(response)
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    run_demo()
