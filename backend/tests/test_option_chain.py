"""
Tests for Indian Equity Option Chain Feature
- GET /api/option-chain/equity/{symbol}  : Equity option chain (NSE live + BS fallback)
- GET /api/option/equity-intraday        : Equity option intraday bars (BS-synthesized)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestEquityOptionChain:
    """Tests for /api/option-chain/equity/{symbol}"""

    def test_option_chain_reliance_status(self):
        """Equity option chain for RELIANCE returns 200"""
        url = f"{BASE_URL}/api/option-chain/equity/RELIANCE"
        r = requests.get(url, timeout=30)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"

    def test_option_chain_reliance_structure(self):
        """Response has required top-level keys"""
        url = f"{BASE_URL}/api/option-chain/equity/RELIANCE"
        r = requests.get(url, timeout=30)
        assert r.status_code == 200
        data = r.json()
        required_keys = ["symbol", "underlying_price", "nearest_expiry", "all_expiries", "atm_strike", "chain"]
        for key in required_keys:
            assert key in data, f"Missing key: {key}"

    def test_option_chain_reliance_chain_array(self):
        """chain array is non-empty list of {strike, call, put} objects"""
        url = f"{BASE_URL}/api/option-chain/equity/RELIANCE"
        r = requests.get(url, timeout=30)
        assert r.status_code == 200
        data = r.json()
        chain = data.get("chain", [])
        assert isinstance(chain, list), "chain must be a list"
        assert len(chain) > 0, "chain array must not be empty"
        # Check structure of first row
        row = chain[0]
        assert "strike" in row, "chain row must have 'strike'"
        assert "call" in row or "put" in row, "chain row must have 'call' or 'put'"

    def test_option_chain_reliance_call_put_pairs(self):
        """Chain rows have both call and put entries (or at least one side)"""
        url = f"{BASE_URL}/api/option-chain/equity/RELIANCE"
        r = requests.get(url, timeout=30)
        assert r.status_code == 200
        data = r.json()
        chain = data.get("chain", [])
        assert len(chain) >= 5, "Expected at least 5 strike rows"
        # Find ATM row
        atm_strike = data.get("atm_strike")
        atm_row = next((r for r in chain if r["strike"] == atm_strike), None)
        if atm_row:
            # ATM row should have both call and put
            assert atm_row.get("call") is not None or atm_row.get("put") is not None, \
                "ATM row must have call or put data"

    def test_option_chain_reliance_underlying_price(self):
        """underlying_price should be positive"""
        url = f"{BASE_URL}/api/option-chain/equity/RELIANCE"
        r = requests.get(url, timeout=30)
        assert r.status_code == 200
        data = r.json()
        price = data.get("underlying_price", 0)
        assert float(price) > 0, f"underlying_price must be positive, got {price}"

    def test_option_chain_reliance_expiries(self):
        """nearest_expiry and all_expiries should be non-empty"""
        url = f"{BASE_URL}/api/option-chain/equity/RELIANCE"
        r = requests.get(url, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("nearest_expiry"), "nearest_expiry must be non-null"
        all_exp = data.get("all_expiries", [])
        assert isinstance(all_exp, list), "all_expiries must be a list"
        assert len(all_exp) > 0, "all_expiries must have at least 1 entry"

    def test_option_chain_reliance_atm_strike(self):
        """atm_strike should be in the chain"""
        url = f"{BASE_URL}/api/option-chain/equity/RELIANCE"
        r = requests.get(url, timeout=30)
        assert r.status_code == 200
        data = r.json()
        atm = data.get("atm_strike", 0)
        assert atm and float(atm) > 0, f"atm_strike must be positive, got {atm}"
        # atm should appear in chain
        chain = data.get("chain", [])
        strikes_in_chain = [row["strike"] for row in chain]
        assert float(atm) in strikes_in_chain, f"atm_strike {atm} not found in chain strikes"

    def test_option_chain_call_price_positive(self):
        """Call prices should be positive floats"""
        url = f"{BASE_URL}/api/option-chain/equity/RELIANCE"
        r = requests.get(url, timeout=30)
        assert r.status_code == 200
        data = r.json()
        chain = data.get("chain", [])
        call_rows = [row for row in chain if row.get("call")]
        assert len(call_rows) > 0, "Should have at least one call row"
        first_call = call_rows[0]["call"]
        assert "last_price" in first_call, "call must have last_price"
        assert float(first_call["last_price"]) >= 0, "call last_price must be >= 0"

    def test_option_chain_put_price_positive(self):
        """Put prices should be positive floats"""
        url = f"{BASE_URL}/api/option-chain/equity/RELIANCE"
        r = requests.get(url, timeout=30)
        assert r.status_code == 200
        data = r.json()
        chain = data.get("chain", [])
        put_rows = [row for row in chain if row.get("put")]
        assert len(put_rows) > 0, "Should have at least one put row"
        first_put = put_rows[0]["put"]
        assert "last_price" in first_put, "put must have last_price"
        assert float(first_put["last_price"]) >= 0, "put last_price must be >= 0"

    def test_option_chain_with_expiry_param(self):
        """Passing expiry param should return 200 and matching expiry in response"""
        # First get the nearest expiry
        url = f"{BASE_URL}/api/option-chain/equity/RELIANCE"
        r = requests.get(url, timeout=30)
        assert r.status_code == 200
        data = r.json()
        nearest = data.get("nearest_expiry")
        if not nearest:
            pytest.skip("No nearest_expiry returned")

        # Now query with that expiry
        r2 = requests.get(f"{BASE_URL}/api/option-chain/equity/RELIANCE", params={"expiry": nearest}, timeout=30)
        assert r2.status_code == 200
        data2 = r2.json()
        assert len(data2.get("chain", [])) > 0, "chain must not be empty when queried with valid expiry"

    def test_option_chain_tcs(self):
        """TCS option chain also returns 200 with data"""
        url = f"{BASE_URL}/api/option-chain/equity/TCS"
        r = requests.get(url, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert len(data.get("chain", [])) > 0

    def test_option_chain_with_ns_suffix(self):
        """Symbol with .NS suffix should also work"""
        url = f"{BASE_URL}/api/option-chain/equity/RELIANCE.NS"
        r = requests.get(url, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("symbol") == "RELIANCE", f"Expected symbol=RELIANCE, got {data.get('symbol')}"


class TestEquityOptionIntraday:
    """Tests for /api/option/equity-intraday"""

    def _get_test_params(self):
        """Get test parameters from option chain response"""
        url = f"{BASE_URL}/api/option-chain/equity/RELIANCE"
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            return None
        data = r.json()
        atm = data.get("atm_strike")
        expiry = data.get("nearest_expiry")
        if not atm or not expiry:
            return None
        return {"underlying": "RELIANCE", "strike": atm, "expiry": expiry}

    def test_equity_intraday_ce_status(self):
        """CE option intraday returns 200"""
        params = self._get_test_params()
        if not params:
            pytest.skip("Could not get test params from option chain")
        r = requests.get(f"{BASE_URL}/api/option/equity-intraday", params={
            **params,
            "option_type": "CE",
            "interval_min": 5,
        }, timeout=30)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"

    def test_equity_intraday_pe_status(self):
        """PE option intraday returns 200"""
        params = self._get_test_params()
        if not params:
            pytest.skip("Could not get test params from option chain")
        r = requests.get(f"{BASE_URL}/api/option/equity-intraday", params={
            **params,
            "option_type": "PE",
            "interval_min": 5,
        }, timeout=30)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"

    def test_equity_intraday_bars_structure(self):
        """Response has ticker and bars array"""
        params = self._get_test_params()
        if not params:
            pytest.skip("Could not get test params")
        r = requests.get(f"{BASE_URL}/api/option/equity-intraday", params={
            **params,
            "option_type": "CE",
            "interval_min": 5,
        }, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "ticker" in data, "Response must have 'ticker'"
        assert "bars" in data, "Response must have 'bars'"
        assert isinstance(data["bars"], list), "'bars' must be a list"

    def test_equity_intraday_bars_non_empty(self):
        """Bars array should have at least 1 bar"""
        params = self._get_test_params()
        if not params:
            pytest.skip("Could not get test params")
        r = requests.get(f"{BASE_URL}/api/option/equity-intraday", params={
            **params,
            "option_type": "CE",
            "interval_min": 5,
        }, timeout=30)
        assert r.status_code == 200
        data = r.json()
        bars = data.get("bars", [])
        assert len(bars) > 0, "bars array must not be empty"

    def test_equity_intraday_bar_ohlc(self):
        """Each bar has OHLC + timestamp"""
        params = self._get_test_params()
        if not params:
            pytest.skip("Could not get test params")
        r = requests.get(f"{BASE_URL}/api/option/equity-intraday", params={
            **params,
            "option_type": "CE",
            "interval_min": 5,
        }, timeout=30)
        assert r.status_code == 200
        data = r.json()
        bars = data.get("bars", [])
        if not bars:
            pytest.skip("No bars returned")
        bar = bars[0]
        for field in ["timestamp", "open", "high", "low", "close"]:
            assert field in bar, f"Bar missing field: {field}"
        assert float(bar["high"]) >= float(bar["low"]), "high must be >= low"
        assert float(bar["close"]) > 0, "close must be positive"

    def test_equity_intraday_ticker_format(self):
        """Ticker in response should include instrument details"""
        params = self._get_test_params()
        if not params:
            pytest.skip("Could not get test params")
        r = requests.get(f"{BASE_URL}/api/option/equity-intraday", params={
            **params,
            "option_type": "CE",
            "interval_min": 5,
        }, timeout=30)
        assert r.status_code == 200
        data = r.json()
        ticker = data.get("ticker", "")
        assert len(ticker) > 0, "ticker must be non-empty"

    def test_equity_intraday_invalid_option_type(self):
        """Invalid option_type returns 422"""
        params = self._get_test_params()
        if not params:
            pytest.skip("Could not get test params")
        r = requests.get(f"{BASE_URL}/api/option/equity-intraday", params={
            **params,
            "option_type": "INVALID",
            "interval_min": 5,
        }, timeout=15)
        assert r.status_code in [400, 422], f"Expected 400 or 422, got {r.status_code}"

    def test_equity_intraday_missing_params(self):
        """Missing required params returns 422"""
        r = requests.get(f"{BASE_URL}/api/option/equity-intraday", timeout=10)
        assert r.status_code == 422, f"Expected 422, got {r.status_code}"

    def test_equity_intraday_manual_strike(self):
        """Test with manual strike=1300 and explicit expiry format"""
        # First get a valid expiry
        chain_r = requests.get(f"{BASE_URL}/api/option-chain/equity/RELIANCE", timeout=30)
        if chain_r.status_code != 200:
            pytest.skip("Can't get expiry")
        expiry = chain_r.json().get("nearest_expiry")
        if not expiry:
            pytest.skip("No nearest_expiry")
        r = requests.get(f"{BASE_URL}/api/option/equity-intraday", params={
            "underlying": "RELIANCE",
            "strike": 1300,
            "option_type": "CE",
            "expiry": expiry,
            "interval_min": 5,
        }, timeout=30)
        # Should succeed or return 404 if no data available; not a 500
        assert r.status_code != 500, f"Got 500 server error: {r.text[:300]}"
        assert r.status_code in [200, 404], f"Got unexpected status: {r.status_code}"
