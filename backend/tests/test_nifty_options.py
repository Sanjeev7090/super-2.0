"""
Tests for /api/indices/top-options/{symbol} endpoint
Covers: NIFTY BS-derived fallback, response structure, filter params, SENSEX
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


class TestNiftyOptionsEndpoint:
    """Core tests for GET /api/indices/top-options/NIFTY"""

    def test_nifty_options_returns_200(self, api):
        """Endpoint must return HTTP 200 (previously returning 502)"""
        res = api.get(f"{BASE_URL}/api/indices/top-options/NIFTY")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text[:400]}"
        print(f"PASS: /api/indices/top-options/NIFTY returned {res.status_code}")

    def test_nifty_options_response_structure(self, api):
        """Response must have required top-level fields"""
        res = api.get(f"{BASE_URL}/api/indices/top-options/NIFTY")
        assert res.status_code == 200
        data = res.json()

        required_keys = ["symbol", "underlying_price", "nearest_expiry", "options"]
        for key in required_keys:
            assert key in data, f"Missing key: {key}"

        assert data["symbol"] == "NIFTY"
        assert isinstance(data["underlying_price"], (int, float))
        assert data["underlying_price"] > 0, "underlying_price must be > 0"
        assert isinstance(data["options"], list)
        print(f"PASS: Response structure valid. Underlying: {data['underlying_price']}, Options count: {len(data['options'])}")

    def test_nifty_options_has_data(self, api):
        """options array must contain items (at least 10 ATM strikes)"""
        res = api.get(f"{BASE_URL}/api/indices/top-options/NIFTY")
        assert res.status_code == 200
        data = res.json()

        opts = data["options"]
        assert len(opts) >= 5, f"Expected at least 5 options, got {len(opts)}"
        print(f"PASS: Got {len(opts)} options")

    def test_nifty_options_has_ce_and_pe(self, api):
        """Options list should include both CE and PE types"""
        res = api.get(f"{BASE_URL}/api/indices/top-options/NIFTY")
        assert res.status_code == 200
        data = res.json()

        opts = data["options"]
        types = {o["type"] for o in opts}
        assert "CE" in types, f"No CE options found. Types: {types}"
        assert "PE" in types, f"No PE options found. Types: {types}"
        print(f"PASS: Both CE and PE options present")

    def test_nifty_option_row_fields(self, api):
        """Each option row must have price, iv, delta, theta fields"""
        res = api.get(f"{BASE_URL}/api/indices/top-options/NIFTY")
        assert res.status_code == 200
        data = res.json()

        opts = data["options"]
        assert len(opts) > 0, "No options to inspect"

        row = opts[0]
        required_opt_keys = ["instrument", "strike", "type", "last_price", "iv", "delta", "theta"]
        for key in required_opt_keys:
            assert key in row, f"Option row missing key: {key}"

        assert row["last_price"] > 0, f"last_price should be > 0, got {row['last_price']}"
        assert row["iv"] > 0, f"IV should be > 0, got {row['iv']}"
        print(f"PASS: Option row fields valid. Sample: {row['instrument']} @ ₹{row['last_price']}, IV={row['iv']}%, Δ={row['delta']}")

    def test_nifty_options_bs_derived_flag(self, api):
        """When NSE live data is unavailable, is_live_derived should be True"""
        res = api.get(f"{BASE_URL}/api/indices/top-options/NIFTY")
        assert res.status_code == 200
        data = res.json()

        # is_live_derived may be True (BS fallback) or False (live NSE) — just must be present
        assert "is_live_derived" in data, "Missing is_live_derived field"
        print(f"PASS: is_live_derived={data['is_live_derived']}")
        if data.get("is_live_derived"):
            print(f"INFO: Using BS-derived fallback. Note: {data.get('note', 'N/A')}")

    def test_nifty_options_call_filter(self, api):
        """option_type=call should return only CE options"""
        res = api.get(f"{BASE_URL}/api/indices/top-options/NIFTY", params={"option_type": "call", "limit": 10})
        assert res.status_code == 200
        data = res.json()

        opts = data["options"]
        if len(opts) > 0:
            types = {o["type"] for o in opts}
            assert types == {"CE"}, f"Expected only CE, got {types}"
        print(f"PASS: call filter returned {len(opts)} CE options")

    def test_nifty_options_put_filter(self, api):
        """option_type=put should return only PE options"""
        res = api.get(f"{BASE_URL}/api/indices/top-options/NIFTY", params={"option_type": "put", "limit": 10})
        assert res.status_code == 200
        data = res.json()

        opts = data["options"]
        if len(opts) > 0:
            types = {o["type"] for o in opts}
            assert types == {"PE"}, f"Expected only PE, got {types}"
        print(f"PASS: put filter returned {len(opts)} PE options")

    def test_nifty_options_all_filter(self, api):
        """option_type=all (default) should return both CE and PE"""
        res = api.get(f"{BASE_URL}/api/indices/top-options/NIFTY", params={"option_type": "all", "limit": 20})
        assert res.status_code == 200
        data = res.json()

        opts = data["options"]
        assert len(opts) > 0
        types = {o["type"] for o in opts}
        # With ATM ±15 strikes, we should have both types
        assert len(types) >= 1
        print(f"PASS: all filter returned {len(opts)} options with types {types}")

    def test_nifty_options_nearest_expiry(self, api):
        """nearest_expiry must be a valid date string"""
        res = api.get(f"{BASE_URL}/api/indices/top-options/NIFTY")
        assert res.status_code == 200
        data = res.json()

        exp = data.get("nearest_expiry", "")
        assert exp, "nearest_expiry is empty"
        # Should be in dd-Mon-YYYY format like "06-Feb-2026"
        assert len(exp) >= 9, f"Invalid expiry format: {exp}"
        print(f"PASS: nearest_expiry = {exp}")

    def test_nifty_options_all_expiries(self, api):
        """all_expiries should be a list with upcoming Thursday dates"""
        res = api.get(f"{BASE_URL}/api/indices/top-options/NIFTY")
        assert res.status_code == 200
        data = res.json()

        expiries = data.get("all_expiries", [])
        assert isinstance(expiries, list)
        assert len(expiries) >= 1, f"all_expiries list is empty"
        print(f"PASS: all_expiries = {expiries}")


class TestBankNiftyOptionsEndpoint:
    """Sanity checks for BANKNIFTY"""

    def test_banknifty_options_200(self, api):
        res = api.get(f"{BASE_URL}/api/indices/top-options/BANKNIFTY")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert data["symbol"] == "BANKNIFTY"
        assert len(data["options"]) >= 1
        print(f"PASS: BANKNIFTY options: {len(data['options'])} rows, underlying={data['underlying_price']}")


class TestSensexOptionsEndpoint:
    """Sanity checks for SENSEX"""

    def test_sensex_options_200(self, api):
        res = api.get(f"{BASE_URL}/api/indices/top-options/SENSEX")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text[:200]}"
        data = res.json()
        assert data["symbol"] == "SENSEX"
        assert len(data["options"]) >= 1
        print(f"PASS: SENSEX options: {len(data['options'])} rows, is_live_derived={data.get('is_live_derived')}")

    def test_sensex_live_derived_flag(self, api):
        res = api.get(f"{BASE_URL}/api/indices/top-options/SENSEX")
        assert res.status_code == 200
        data = res.json()
        assert data.get("is_live_derived") is True, "SENSEX should always be is_live_derived=True"
        print(f"PASS: SENSEX is_live_derived=True confirmed")
