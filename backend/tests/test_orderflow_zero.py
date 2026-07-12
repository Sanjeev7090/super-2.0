"""
Test suite for OrderFlow analyze endpoint with zero/near-zero price scenarios.
Bug: ZeroDivisionError when bars have all-zero prices (_of_volume_profile, _of_calc_atr).
Fix verified: price_max guard, bin_size <= 0 guard, max(avg, 0.01) in ATR, rng guard in footprint.
"""

import pytest
import requests
import os
import math

# Use public URL if available, fallback to localhost for direct backend testing
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")

ENDPOINT = f"{BASE_URL}/api/orderflow/analyze"


def make_zero_bars(n=35):
    """35 bars all with price=0.0 and volume=0."""
    bars = []
    for i in range(n):
        bars.append({
            "timestamp": 1720000000000 + i * 60000,
            "open": 0.0,
            "high": 0.0,
            "low": 0.0,
            "close": 0.0,
            "volume": 0,
        })
    return bars


def make_tiny_price_bars(n=35):
    """35 bars with very small option prices (0.01-0.05 range)."""
    bars = []
    prices = [0.01, 0.02, 0.03, 0.04, 0.05]
    for i in range(n):
        p = prices[i % len(prices)]
        bars.append({
            "timestamp": 1720000000000 + i * 60000,
            "open": p,
            "high": p + 0.01,
            "low": max(p - 0.01, 0.0),
            "close": p,
            "volume": 100,
        })
    return bars


def make_mixed_bars(n=35):
    """Mixed bars: first 30 all-zero, last 5 with small prices."""
    bars = []
    for i in range(30):
        bars.append({
            "timestamp": 1720000000000 + i * 60000,
            "open": 0.0, "high": 0.0, "low": 0.0, "close": 0.0, "volume": 0,
        })
    for i in range(30, n):
        bars.append({
            "timestamp": 1720000000000 + i * 60000,
            "open": 0.02, "high": 0.04, "low": 0.01, "close": 0.03, "volume": 100,
        })
    return bars


def base_payload(bars, ticker="NIFTY24200CE"):
    return {
        "ticker": ticker,
        "bars": bars,
        "n_vp_bins": 30,
        "n_fp_levels": 8,
        "vp_lookback": 35,
    }


class TestOrderFlowZeroPrice:
    """Tests for OrderFlow analyze endpoint with zero/near-zero price bars."""

    def test_all_zero_bars_returns_200(self):
        """35 bars all zero — must NOT return 500 ZeroDivisionError."""
        payload = base_payload(make_zero_bars(35))
        resp = requests.post(ENDPOINT, json=payload, timeout=30)
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}. Body: {resp.text[:500]}"
        )
        print("PASS: all-zero bars returns 200")

    def test_all_zero_bars_valid_signal(self):
        """35 bars all zero — response must contain a valid signal."""
        payload = base_payload(make_zero_bars(35))
        resp = requests.post(ENDPOINT, json=payload, timeout=30)
        assert resp.status_code == 200
        data = resp.json()
        assert "signal_type" in data, "Missing signal_type in response"
        assert data["signal_type"] in ("BUY", "SELL", "WAIT"), (
            f"Unexpected signal_type: {data['signal_type']}"
        )
        print(f"PASS: all-zero bars signal={data['signal_type']}")

    def test_all_zero_bars_atr_positive(self):
        """ATR must be > 0 even when all prices are zero (never causes downstream div/0)."""
        payload = base_payload(make_zero_bars(35))
        resp = requests.post(ENDPOINT, json=payload, timeout=30)
        assert resp.status_code == 200
        data = resp.json()
        atr = data.get("atr", 0)
        assert atr > 0, f"ATR must be > 0, got {atr}"
        print(f"PASS: ATR={atr} > 0 for all-zero bars")

    def test_all_zero_bars_poc_finite(self):
        """poc_price / vah_price / val_price must be finite numbers, not NaN/Infinity."""
        payload = base_payload(make_zero_bars(35))
        resp = requests.post(ENDPOINT, json=payload, timeout=30)
        assert resp.status_code == 200
        data = resp.json()
        poc = data.get("poc_price")
        vah = data.get("vah_price")
        val = data.get("val_price")
        for name, val_num in [("poc_price", poc), ("vah_price", vah), ("val_price", val)]:
            if val_num is not None:
                assert math.isfinite(float(val_num)), f"{name}={val_num} is not finite"
        print(f"PASS: poc={poc}, vah={vah}, val={val} — all finite")

    def test_tiny_price_bars_returns_200(self):
        """35 bars with 0.01-0.05 prices — must return 200."""
        payload = base_payload(make_tiny_price_bars(35))
        resp = requests.post(ENDPOINT, json=payload, timeout=30)
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}. Body: {resp.text[:500]}"
        )
        print("PASS: tiny price bars returns 200")

    def test_tiny_price_bars_valid_signal(self):
        """Tiny option prices — response must have valid signal and atr > 0."""
        payload = base_payload(make_tiny_price_bars(35))
        resp = requests.post(ENDPOINT, json=payload, timeout=30)
        assert resp.status_code == 200
        data = resp.json()
        assert data["signal_type"] in ("BUY", "SELL", "WAIT")
        atr = data.get("atr", 0)
        assert atr > 0, f"ATR must be > 0 for tiny prices, got {atr}"
        print(f"PASS: tiny prices signal={data['signal_type']}, ATR={atr}")

    def test_mixed_zero_and_tiny_bars_returns_200(self):
        """30 zero bars + 5 tiny bars — must return 200 without ZeroDivisionError."""
        payload = base_payload(make_mixed_bars(35))
        resp = requests.post(ENDPOINT, json=payload, timeout=30)
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}. Body: {resp.text[:500]}"
        )
        print("PASS: mixed zero+tiny bars returns 200")

    def test_mixed_bars_atr_positive(self):
        """Mixed bars — ATR must be > 0."""
        payload = base_payload(make_mixed_bars(35))
        resp = requests.post(ENDPOINT, json=payload, timeout=30)
        assert resp.status_code == 200
        data = resp.json()
        atr = data.get("atr", 0)
        assert atr > 0, f"ATR must be > 0 for mixed bars, got {atr}"
        print(f"PASS: mixed bars ATR={atr} > 0")

    def test_too_few_bars_returns_400(self):
        """Fewer than 30 bars should return 400 (validation guard)."""
        payload = base_payload(make_zero_bars(10))
        resp = requests.post(ENDPOINT, json=payload, timeout=30)
        assert resp.status_code == 400, (
            f"Expected 400 for <30 bars, got {resp.status_code}"
        )
        print("PASS: <30 bars returns 400")

    def test_pre_existing_test_payload_from_tmp(self):
        """
        Reproduce exact bug scenario from /tmp/test_orderflow.json:
        30 zero bars + 5 tiny bars (open=0.02, high=0.04, low=0.01, close=0.03, vol=100).
        """
        import json
        with open("/tmp/test_orderflow.json") as f:
            payload = json.load(f)
        resp = requests.post(ENDPOINT, json=payload, timeout=30)
        assert resp.status_code == 200, (
            f"Original bug payload still failing! status={resp.status_code}. "
            f"Body: {resp.text[:500]}"
        )
        data = resp.json()
        assert data["signal_type"] in ("BUY", "SELL", "WAIT")
        atr = data.get("atr", 0)
        assert atr > 0, f"ATR still 0 in original bug payload!"
        print(f"PASS: original bug payload: signal={data['signal_type']}, ATR={atr}")
        print(f"  poc={data.get('poc_price')}, vah={data.get('vah_price')}, val={data.get('val_price')}")

    def test_all_zero_bars_response_structure(self):
        """Validate full response structure for zero-price scenario."""
        payload = base_payload(make_zero_bars(35))
        resp = requests.post(ENDPOINT, json=payload, timeout=30)
        assert resp.status_code == 200
        data = resp.json()
        required_fields = [
            "ticker", "signal_type", "signal_strength", "atr",
            "buy_pct", "sell_pct", "current_delta", "current_cvd",
            "cvd_slope", "divergence",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        assert data["ticker"] == "NIFTY24200CE"
        print(f"PASS: response structure valid. signal={data['signal_type']}, strength={data['signal_strength']}")

    def test_no_division_by_zero_in_error_message(self):
        """Confirm error message does NOT contain 'float division by zero'."""
        payload = base_payload(make_zero_bars(35))
        resp = requests.post(ENDPOINT, json=payload, timeout=30)
        # Should be 200; but even if it's not, check the error isn't the ZeroDivisionError
        body = resp.text
        assert "float division by zero" not in body.lower(), (
            f"ZeroDivisionError still present! Response: {body[:500]}"
        )
        assert resp.status_code == 200
        print("PASS: No 'float division by zero' in response")
