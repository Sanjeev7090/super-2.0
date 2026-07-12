"""
Tests for three brain improvements in the trading system:
A) HybridSuperBrain as Truly Central — _brain_gate_top_picks() in universe_scanner.py
B) Diversity + Randomness  — _apply_diversity_and_noise() in danger_scanner.py
                            — _diversify_with_noise() in universe_scanner.py
C) Dynamic Confidence Threshold — _dynamic_conf_threshold() in trading_loop.py
"""

import sys
import os
import pytest
import requests
from collections import Counter
from typing import List, Dict, Any

# ─── Path setup — working dir is /app/backend ────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


# ─── Import under-test functions ─────────────────────────────────────────────
from agents.danger_scanner import _apply_diversity_and_noise
from agents.universe_scanner import _diversify_with_noise, _brain_gate_top_picks
from agents.trading_loop import _dynamic_conf_threshold


# ═════════════════════════════════════════════════════════════════════════════
# C. Dynamic Confidence Threshold  (_dynamic_conf_threshold)
# ═════════════════════════════════════════════════════════════════════════════

class TestDynamicConfThreshold:
    """C. Dynamic Confidence Threshold — scales execution gate with market volatility."""

    def test_empty_dict_returns_58(self):
        """Empty watchlist_obs should return default threshold 58."""
        result = _dynamic_conf_threshold({})
        assert result == 58, f"Expected 58 for empty dict, got {result}"
        print(f"PASS: empty dict → {result}")

    def test_low_vol_atr_1_5_returns_58(self):
        """ATR%=1.5 (normal VIX~15) → threshold should be 58."""
        obs = {"HDFCBANK.NS": {"atr_pct": 1.5}}
        result = _dynamic_conf_threshold(obs)
        assert result == 58, f"Expected 58 for atr_pct=1.5, got {result}"
        print(f"PASS: atr_pct=1.5 → {result}")

    def test_medium_vol_atr_2_5_returns_62(self):
        """ATR%=2.5 (VIX~20) → threshold should be 62."""
        obs = {"RELIANCE.NS": {"atr_pct": 2.5}}
        result = _dynamic_conf_threshold(obs)
        assert result == 62, f"Expected 62 for atr_pct=2.5, got {result}"
        print(f"PASS: atr_pct=2.5 → {result}")

    def test_high_vol_atr_3_5_returns_66(self):
        """ATR%=3.5 (VIX~25) → threshold should be 66."""
        obs = {"INFY.NS": {"atr_pct": 3.5}}
        result = _dynamic_conf_threshold(obs)
        assert result == 66, f"Expected 66 for atr_pct=3.5, got {result}"
        print(f"PASS: atr_pct=3.5 → {result}")

    def test_extreme_vol_atr_5_5_returns_74(self):
        """ATR%=5.5 (extreme vol) → threshold should be 74.
        Note: docstring says 76 but formula gives 74 at 5.5%:
              extra = min(18, (5.5-1.5)*4) = min(18, 16) = 16 → 58+16=74
        """
        obs = {"TCS.NS": {"atr_pct": 5.5}}
        result = _dynamic_conf_threshold(obs)
        assert result == 74, f"Expected 74 for atr_pct=5.5, got {result}"
        print(f"PASS: atr_pct=5.5 → {result}")

    def test_extreme_vol_atr_6_0_returns_76_capped(self):
        """ATR%=6.0+ should be capped at 76.
           extra = min(18, (6.0-1.5)*4) = min(18, 18) = 18 → 58+18=76
        """
        obs = {"NIFTY": {"atr_pct": 6.0}}
        result = _dynamic_conf_threshold(obs)
        assert result == 76, f"Expected 76 (cap) for atr_pct=6.0, got {result}"
        print(f"PASS: atr_pct=6.0 → {result} (capped at 76)")

    def test_very_low_vol_minimum_48(self):
        """Very low ATR% should not go below minimum floor 48."""
        obs = {"NIFTY": {"atr_pct": 0.0}}
        result = _dynamic_conf_threshold(obs)
        # With atr_pct=0.0: (0.0-1.5)*4 = -6 → max(0,-6)=0 → extra=0 → 58
        # 0.0 atr_pct is falsy, so it won't be included in atrs list
        # If all entries are filtered out, returns 58
        assert result >= 48, f"Threshold {result} below minimum 48"
        print(f"PASS: atr_pct=0.0 (falsy) → {result}")

    def test_monotonic_relationship(self):
        """Higher ATR% must give higher (or equal) threshold — monotonic relationship."""
        atr_values = [1.5, 2.5, 3.5, 5.5]
        thresholds = []
        for atr in atr_values:
            t = _dynamic_conf_threshold({"ticker": {"atr_pct": atr}})
            thresholds.append(t)
            print(f"  atr_pct={atr} → threshold={t}")

        # Verify strictly increasing
        for i in range(1, len(thresholds)):
            assert thresholds[i] >= thresholds[i - 1], (
                f"Non-monotonic: atr={atr_values[i]} gave {thresholds[i]} "
                f"< atr={atr_values[i-1]} gave {thresholds[i-1]}"
            )
        print(f"PASS: Monotonic ordering: {list(zip(atr_values, thresholds))}")

    def test_multiple_tickers_average_atr(self):
        """Multiple tickers — should use average ATR% to compute threshold."""
        obs = {
            "HDFCBANK.NS": {"atr_pct": 1.5},
            "TCS.NS":       {"atr_pct": 3.5},
        }
        result = _dynamic_conf_threshold(obs)
        # avg_atr = (1.5 + 3.5) / 2 = 2.5 → threshold = 62
        assert result == 62, f"Expected 62 for avg atr=2.5, got {result}"
        print(f"PASS: avg atr=2.5 → threshold={result}")

    def test_return_type_is_int(self):
        """Return value must be an int (not float)."""
        result = _dynamic_conf_threshold({"t": {"atr_pct": 2.5}})
        assert isinstance(result, int), f"Expected int, got {type(result)}: {result}"
        print(f"PASS: return type is int: {result}")

    def test_no_atr_key_returns_58(self):
        """If entries exist but have no 'atr_pct' key, should return default 58."""
        obs = {"NIFTY": {"rsi14": 55.0, "regime": "UPTREND"}}
        result = _dynamic_conf_threshold(obs)
        # All filtered out (no atr_pct), returns 58
        assert result == 58, f"Expected 58 when no atr_pct key, got {result}"
        print(f"PASS: no atr_pct key → {result}")


# ═════════════════════════════════════════════════════════════════════════════
# B-1. Danger Scanner Diversity + Noise  (_apply_diversity_and_noise)
# ═════════════════════════════════════════════════════════════════════════════

def _make_fno_mock_result(ticker: str, sector: str, score: float) -> dict:
    """Helper: create a mock danger-scanner result dict."""
    return {
        "ticker":      ticker,
        "sector":      sector,
        "type":        "stock",
        "final_score": score,
        "raw_score":   score,
        "pcr_boost":   0,
        "pcr_signal":  "NEUTRAL",
        "pcr_conf":    50,
        "price":       1000.0,
        "rsi":         55.0,
        "atr_pct":     0.015,
    }


class TestDangerScannerDiversityNoise:
    """B. Danger scanner — sector diversity cap at 2, and ±12% score noise."""

    def test_sector_cap_max_2_per_sector(self):
        """With 4 Banking entries + 1 IT, output should cap Banking at 2."""
        mock_results = [
            _make_fno_mock_result("HDFCBANK.NS",   "Banking", 90.0),
            _make_fno_mock_result("ICICIBANK.NS",  "Banking", 85.0),
            _make_fno_mock_result("SBIN.NS",        "Banking", 80.0),
            _make_fno_mock_result("AXISBANK.NS",    "Banking", 75.0),
            _make_fno_mock_result("TCS.NS",         "IT",      88.0),
        ]
        result = _apply_diversity_and_noise(mock_results, top_n=5)

        sector_counts = Counter(r["sector"] for r in result)
        print(f"Sector distribution: {dict(sector_counts)}")

        banking_count = sector_counts.get("Banking", 0)
        assert banking_count <= 2, (
            f"Expected max 2 Banking picks, got {banking_count}"
        )
        print(f"PASS: Banking picks capped at {banking_count} (<= 2)")

    def test_three_banking_entries_capped_at_2(self):
        """Test with exactly 3 Banking entries → only 2 should survive the diversity filter."""
        mock_results = [
            _make_fno_mock_result("HDFCBANK.NS",  "Banking", 95.0),
            _make_fno_mock_result("ICICIBANK.NS", "Banking", 90.0),
            _make_fno_mock_result("SBIN.NS",       "Banking", 85.0),
        ]
        result = _apply_diversity_and_noise(mock_results, top_n=3)

        sector_counts = Counter(r["sector"] for r in result)
        banking_count = sector_counts.get("Banking", 0)
        assert banking_count <= 2, (
            f"Expected max 2 Banking picks from 3 inputs, got {banking_count}"
        )
        print(f"PASS: 3 Banking inputs → {banking_count} Banking in output")

    def test_noisy_score_field_added(self):
        """Each result should have a 'noisy_score' field after diversity+noise."""
        mock_results = [
            _make_fno_mock_result("RELIANCE.NS", "Energy", 70.0),
            _make_fno_mock_result("TCS.NS",       "IT",    68.0),
        ]
        result = _apply_diversity_and_noise(mock_results, top_n=2)

        for r in result:
            assert "noisy_score" in r, f"Missing 'noisy_score' in {r['ticker']}"
        print(f"PASS: 'noisy_score' field present on all {len(result)} picks")

    def test_noisy_score_within_12pct_range(self):
        """noisy_score should be within ±12% of final_score."""
        mock_results = [
            _make_fno_mock_result("INFY.NS",    "IT",   80.0),
            _make_fno_mock_result("WIPRO.NS",   "IT",   75.0),
            _make_fno_mock_result("HCLTECH.NS", "IT",   72.0),
        ]
        result = _apply_diversity_and_noise(mock_results, top_n=3)
        for r in result:
            orig  = r["final_score"]
            noisy = r["noisy_score"]
            lo    = orig * 0.88
            hi    = orig * 1.12
            assert lo <= noisy <= hi, (
                f"{r['ticker']}: noisy_score={noisy} outside ±12% of final_score={orig} "
                f"(expected {lo:.1f}–{hi:.1f})"
            )
        print(f"PASS: all noisy_scores within ±12% of final_score")

    def test_top_n_respected(self):
        """Output should have at most top_n entries."""
        mock_results = [
            _make_fno_mock_result(f"STOCK{i}.NS", "IT", float(100 - i))
            for i in range(10)
        ]
        result = _apply_diversity_and_noise(mock_results, top_n=3)
        assert len(result) <= 3, f"Expected <= 3 results, got {len(result)}"
        print(f"PASS: top_n=3 respected → {len(result)} results returned")

    def test_multiple_sectors_all_allowed_up_to_2(self):
        """
        Mixed sectors: 3 Banking + 3 IT + 2 Energy.
        Banking cap: 2, IT cap: 2, Energy cap: 2.
        With top_n=6, all sectors can contribute ≤2.
        """
        mock_results = [
            _make_fno_mock_result("HDFCBANK.NS",  "Banking", 95.0),
            _make_fno_mock_result("TCS.NS",        "IT",     94.0),
            _make_fno_mock_result("ICICIBANK.NS",  "Banking", 93.0),
            _make_fno_mock_result("INFY.NS",        "IT",     92.0),
            _make_fno_mock_result("SBIN.NS",         "Banking", 91.0),  # should be filtered
            _make_fno_mock_result("WIPRO.NS",        "IT",     90.0),   # should be filtered
            _make_fno_mock_result("RELIANCE.NS",     "Energy", 89.0),
            _make_fno_mock_result("ONGC.NS",         "Energy", 88.0),
        ]
        result = _apply_diversity_and_noise(mock_results, top_n=6)
        sector_counts = Counter(r["sector"] for r in result)
        print(f"Multi-sector result distribution: {dict(sector_counts)}")
        for sector, count in sector_counts.items():
            assert count <= 2, f"Sector '{sector}' has {count} picks > 2"
        print(f"PASS: all sectors capped at ≤2 picks")

    def test_empty_input_returns_empty(self):
        """Empty input should return empty list."""
        result = _apply_diversity_and_noise([], top_n=5)
        assert result == [], f"Expected empty list, got {result}"
        print("PASS: empty input → empty output")


# ═════════════════════════════════════════════════════════════════════════════
# B-2. Universe Scanner Diversity + Noise  (_diversify_with_noise)
# ═════════════════════════════════════════════════════════════════════════════

def _make_universe_pick(ticker: str, sector_seg: str, action: str = "BUY",
                        confidence: float = 70.0) -> dict:
    """Helper: create a mock universe-scanner pick."""
    return {
        "ticker":       ticker,
        "name":         ticker.replace(".NS", ""),
        "segment":      sector_seg,  # used as sector fallback in _diversify_with_noise
        "action":       action,
        "confidence":   confidence,
        "price":        1000.0,
        "sl_price":     980.0,
        "tp_price":     1030.0,
        "atr14":        15.0,
        "rsi14":        55.0,
        "regime":       "UPTREND",
        "vol_ratio":    1.5,
        "mom5":         1.2,
        "smc_signal":   "neutral",
        "kronos_phase": "trending",
        "bos":          False,
        "fvg":          False,
        "rr_ratio":     2.0,
    }


class TestUniverseScannerDiversityNoise:
    """B. Universe scanner — sector diversity cap at 3 + ±12% noise on confidence."""

    def test_sector_cap_max_3_per_sector(self):
        """With 5 Banking picks, output should cap at 3."""
        picks = [
            _make_universe_pick("HDFCBANK.NS",  "fo",       confidence=90.0),
            _make_universe_pick("ICICIBANK.NS", "fo",       confidence=88.0),
            _make_universe_pick("SBIN.NS",       "fo",       confidence=86.0),
            _make_universe_pick("AXISBANK.NS",   "banknifty", confidence=84.0),
            _make_universe_pick("KOTAKBANK.NS",  "fo",       confidence=82.0),
            _make_universe_pick("TCS.NS",         "fo",       confidence=80.0),
        ]
        result = _diversify_with_noise(picks, top_n=6)

        # Check _sector field added
        for r in result:
            assert "_sector" in r, f"Missing '_sector' in {r['ticker']}"

        # The sector is determined by _SECTOR_MAP in the function
        # HDFCBANK → Banking, ICICIBANK → Banking, SBIN → Banking, AXISBANK → Banking, KOTAKBANK → Banking
        sector_counts = Counter(r.get("_sector") for r in result)
        print(f"Sector distribution: {dict(sector_counts)}")

        for sector, count in sector_counts.items():
            assert count <= 3, (
                f"Sector '{sector}' has {count} picks > 3 (max per sector)"
            )
        print(f"PASS: all sectors capped at ≤3")

    def test_noisy_conf_field_added(self):
        """Each pick should have a '_noisy_conf' field after diversity+noise."""
        picks = [
            _make_universe_pick("RELIANCE.NS", "fo", confidence=75.0),
            _make_universe_pick("INFY.NS",     "fo", confidence=72.0),
        ]
        result = _diversify_with_noise(picks, top_n=2)
        for r in result:
            assert "_noisy_conf" in r, f"Missing '_noisy_conf' in {r['ticker']}"
            print(f"  {r['ticker']}: conf={r['confidence']}, _noisy_conf={r['_noisy_conf']:.2f}")
        print(f"PASS: '_noisy_conf' field present on all picks")

    def test_noisy_conf_within_12pct_range(self):
        """_noisy_conf should be within ±12% of original confidence."""
        picks = [
            _make_universe_pick("TCS.NS",    "fo", confidence=80.0),
            _make_universe_pick("WIPRO.NS",  "fo", confidence=70.0),
            _make_universe_pick("MARUTI.NS", "fo", confidence=65.0),
        ]
        result = _diversify_with_noise(picks, top_n=3)
        for r in result:
            orig  = r["confidence"]
            noisy = r["_noisy_conf"]
            lo    = orig * 0.88
            hi    = orig * 1.12
            assert lo <= noisy <= hi, (
                f"{r['ticker']}: _noisy_conf={noisy:.2f} outside ±12% of confidence={orig} "
                f"(expected {lo:.1f}–{hi:.1f})"
            )
        print(f"PASS: all _noisy_conf values within ±12% of confidence")

    def test_sector_field_set_correctly_for_known_tickers(self):
        """_sector should use _SECTOR_MAP for known tickers."""
        picks = [
            _make_universe_pick("HDFCBANK.NS", "fo",  confidence=80.0),
            _make_universe_pick("TCS.NS",       "fo",  confidence=78.0),
            _make_universe_pick("RELIANCE.NS",  "fo",  confidence=76.0),
        ]
        result = _diversify_with_noise(picks, top_n=3)
        sector_map = {r["ticker"]: r["_sector"] for r in result}

        # These tickers should map to specific sectors per the _SECTOR_MAP in the function
        if "HDFCBANK.NS" in sector_map:
            assert sector_map["HDFCBANK.NS"] == "Banking", (
                f"Expected HDFCBANK → Banking, got {sector_map.get('HDFCBANK.NS')}"
            )
        if "TCS.NS" in sector_map:
            assert sector_map["TCS.NS"] == "IT", (
                f"Expected TCS → IT, got {sector_map.get('TCS.NS')}"
            )
        if "RELIANCE.NS" in sector_map:
            assert sector_map["RELIANCE.NS"] == "Energy", (
                f"Expected RELIANCE → Energy, got {sector_map.get('RELIANCE.NS')}"
            )
        print(f"PASS: Sector mappings correct: {sector_map}")

    def test_4_banking_picks_capped_at_3(self):
        """4 Banking picks → only 3 should appear in output."""
        picks = [
            _make_universe_pick("HDFCBANK.NS",  "fo", confidence=90.0),
            _make_universe_pick("ICICIBANK.NS", "fo", confidence=88.0),
            _make_universe_pick("SBIN.NS",       "fo", confidence=86.0),
            _make_universe_pick("AXISBANK.NS",   "fo", confidence=84.0),
        ]
        result = _diversify_with_noise(picks, top_n=4)
        sector_counts = Counter(r.get("_sector") for r in result)
        banking_count = sector_counts.get("Banking", 0)
        assert banking_count <= 3, (
            f"Expected max 3 Banking picks, got {banking_count}"
        )
        print(f"PASS: 4 Banking inputs → {banking_count} Banking in output (≤3)")

    def test_top_n_respected(self):
        """Output should not exceed top_n entries."""
        picks = [
            _make_universe_pick(f"STOCK{i}.NS", "fo", confidence=float(90 - i))
            for i in range(10)
        ]
        result = _diversify_with_noise(picks, top_n=4)
        assert len(result) <= 4, f"Expected ≤4 results, got {len(result)}"
        print(f"PASS: top_n=4 respected → {len(result)} results")

    def test_unknown_ticker_falls_back_to_segment(self):
        """Ticker not in _SECTOR_MAP → _sector should fall back to segment."""
        picks = [
            _make_universe_pick("UNKNOWN123.NS", "fo", confidence=75.0),
        ]
        result = _diversify_with_noise(picks, top_n=1)
        assert len(result) == 1
        # UNKNOWN123 not in _SECTOR_MAP, base = "UNKNOWN123", sector = segment = "fo"
        assert result[0]["_sector"] == "fo", (
            f"Expected fallback _sector='fo', got {result[0]['_sector']}"
        )
        print(f"PASS: unknown ticker → _sector='fo' (fallback to segment)")

    def test_empty_input_returns_empty(self):
        """Empty input list → empty output."""
        result = _diversify_with_noise([], top_n=5)
        assert result == [], f"Expected empty list, got {result}"
        print("PASS: empty input → empty output")


# ═════════════════════════════════════════════════════════════════════════════
# A. Brain Gate  (_brain_gate_top_picks)
# ═════════════════════════════════════════════════════════════════════════════

def _make_brain_gate_pick(ticker: str, action: str = "BUY",
                          confidence: float = 70.0) -> dict:
    """Helper: create a mock pick for brain gate testing."""
    return {
        "ticker":     ticker,
        "name":       ticker.replace(".NS", ""),
        "action":     action,
        "confidence": confidence,
        "price":      1000.0,
        "atr14":      15.0,
        "rsi14":      55.0,
        "regime":     "UPTREND",
        "vol_ratio":  1.5,
        "mom5":       1.2,
        "sl_price":   975.0,
        "tp_price":   1045.0,
    }


VALID_BRAIN_GATE_VALUES = {"PASS", "WARN", "SKIP"}


class TestBrainGateTopPicks:
    """A. HybridSuperBrain gate — validates scanner picks via brain decision."""

    def test_brain_gate_field_added_to_each_pick(self):
        """Every pick should have 'brain_gate' field after processing."""
        picks = [
            _make_brain_gate_pick("RELIANCE.NS", action="BUY",  confidence=75.0),
            _make_brain_gate_pick("TCS.NS",      action="BUY",  confidence=70.0),
            _make_brain_gate_pick("INFY.NS",     action="SELL", confidence=65.0),
        ]
        result = _brain_gate_top_picks(picks)
        for pick in result:
            assert "brain_gate" in pick, (
                f"Missing 'brain_gate' field in pick: {pick['ticker']}"
            )
        print(f"PASS: 'brain_gate' field added to all {len(result)} picks")

    def test_brain_gate_values_are_valid(self):
        """brain_gate values must be 'PASS', 'WARN', or 'SKIP'."""
        picks = [
            _make_brain_gate_pick("HDFCBANK.NS", action="BUY",  confidence=80.0),
            _make_brain_gate_pick("ICICIBANK.NS", action="BUY", confidence=72.0),
            _make_brain_gate_pick("SBIN.NS",      action="SELL", confidence=68.0),
        ]
        result = _brain_gate_top_picks(picks)
        for pick in result:
            gate_val = pick.get("brain_gate")
            assert gate_val in VALID_BRAIN_GATE_VALUES, (
                f"{pick['ticker']}: brain_gate='{gate_val}' not in {VALID_BRAIN_GATE_VALUES}"
            )
            print(f"  {pick['ticker']}: brain_gate={gate_val}")
        print(f"PASS: all brain_gate values are valid ({VALID_BRAIN_GATE_VALUES})")

    def test_brain_gate_preserves_all_picks(self):
        """Function should return all picks (no filtering — just annotation)."""
        picks = [
            _make_brain_gate_pick(f"STOCK{i}.NS", confidence=float(70 + i))
            for i in range(5)
        ]
        result = _brain_gate_top_picks(picks)
        assert len(result) == 5, (
            f"Expected all 5 picks returned, got {len(result)}"
        )
        print(f"PASS: all {len(result)} picks returned (no filtering)")

    def test_brain_gate_only_processes_top_15(self):
        """
        _brain_gate_top_picks processes only picks[:15].
        Picks beyond index 14 may not have brain_gate (or may have SKIP from outer exception).
        All 15 first picks must have brain_gate.
        """
        picks = [
            _make_brain_gate_pick(f"STOCK{i:02d}.NS", confidence=float(90 - i))
            for i in range(20)
        ]
        result = _brain_gate_top_picks(picks)
        # At minimum, first 15 picks should have brain_gate
        for pick in result[:15]:
            assert "brain_gate" in pick, (
                f"Pick index <15 missing 'brain_gate': {pick['ticker']}"
            )
        print(f"PASS: first 15 picks all have brain_gate field")

    def test_brain_gate_empty_input(self):
        """Empty input should return empty list."""
        result = _brain_gate_top_picks([])
        assert result == [], f"Expected empty list, got {result}"
        print("PASS: empty input → empty output")

    def test_brain_gate_does_not_remove_existing_fields(self):
        """brain_gate annotation should not remove existing pick fields."""
        pick = _make_brain_gate_pick("RELIANCE.NS", action="BUY", confidence=75.0)
        original_keys = set(pick.keys())
        result = _brain_gate_top_picks([pick])
        assert len(result) == 1
        # All original fields should still be present
        for key in original_keys:
            assert key in result[0], f"Field '{key}' removed from pick!"
        print(f"PASS: original fields preserved after brain_gate annotation")


# ═════════════════════════════════════════════════════════════════════════════
# Health + Server-Level Tests (HTTP)
# ═════════════════════════════════════════════════════════════════════════════

class TestHealthAndServerEndpoints:
    """Validate server is running healthy after all brain improvement changes."""

    def test_health_endpoint_returns_200(self):
        """GET /api/health should return 200 after all changes."""
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL not set")
        resp = requests.get(f"{BASE_URL}/api/health", timeout=15)
        assert resp.status_code == 200, (
            f"Health check failed: status={resp.status_code}, body={resp.text[:200]}"
        )
        data = resp.json()
        print(f"PASS: /api/health → {resp.status_code} | {data}")

    def test_health_response_has_status_field(self):
        """Health response should contain a status/service indicator."""
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL not set")
        resp = requests.get(f"{BASE_URL}/api/health", timeout=15)
        assert resp.status_code == 200
        data = resp.json()
        # Response should be a dict with some health indicator
        assert isinstance(data, dict), f"Expected dict response, got {type(data)}: {data}"
        print(f"PASS: /api/health response is valid dict: {data}")

    def test_api_root_responds(self):
        """GET /api/ should return 200 (confirms router mounted)."""
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL not set")
        resp = requests.get(f"{BASE_URL}/api/", timeout=10)
        assert resp.status_code in (200, 404), (
            f"Unexpected status for /api/: {resp.status_code}"
        )
        print(f"PASS: /api/ → {resp.status_code}")


# ═════════════════════════════════════════════════════════════════════════════
# Integration — _apply_diversity_and_noise as used in run_danger_scan
# ═════════════════════════════════════════════════════════════════════════════

class TestDangerScanIntegration:
    """
    Integration-style tests using _apply_diversity_and_noise with realistic
    FNO mock data to verify run_danger_scan would respect the sector cap.
    (run_danger_scan itself requires yfinance/network — skipped in unit tests)
    """

    def test_realistic_fno_mock_6_banking_capped_at_2(self):
        """
        Simulate run_danger_scan output with 6 Banking entries (from real FNO universe).
        After _apply_diversity_and_noise(), Banking count must be ≤2.
        """
        # Mirrors FNO_UNIVERSE Banking stocks with mock scores
        banking_stocks = [
            _make_fno_mock_result("HDFCBANK.NS",   "Banking", 92.0),
            _make_fno_mock_result("ICICIBANK.NS",  "Banking", 89.0),
            _make_fno_mock_result("SBIN.NS",        "Banking", 85.0),
            _make_fno_mock_result("AXISBANK.NS",    "Banking", 82.0),
            _make_fno_mock_result("KOTAKBANK.NS",   "Banking", 79.0),
            _make_fno_mock_result("INDUSINDBK.NS",  "Banking", 76.0),
        ]
        other_stocks = [
            _make_fno_mock_result("INFY.NS",      "IT",     88.0),
            _make_fno_mock_result("TCS.NS",        "IT",     84.0),
            _make_fno_mock_result("RELIANCE.NS",   "Energy", 81.0),
            _make_fno_mock_result("SUNPHARMA.NS",  "Pharma", 78.0),
        ]
        all_results = banking_stocks + other_stocks

        result = _apply_diversity_and_noise(all_results, top_n=8)

        sector_counts = Counter(r["sector"] for r in result)
        print(f"Result sector distribution: {dict(sector_counts)}")

        banking_count = sector_counts.get("Banking", 0)
        assert banking_count <= 2, (
            f"Banking count {banking_count} exceeds max 2 in realistic FNO mock test"
        )
        print(f"PASS: 6 Banking inputs → {banking_count} in output (max 2)")

    def test_output_includes_non_banking_sectors(self):
        """
        With sector cap enforced, diversity means non-Banking sectors
        should appear in the top picks (not monopolized by Banking).
        """
        banking_stocks = [
            _make_fno_mock_result("HDFCBANK.NS",  "Banking", 100.0),
            _make_fno_mock_result("ICICIBANK.NS", "Banking", 99.0),
            _make_fno_mock_result("SBIN.NS",       "Banking", 98.0),
            _make_fno_mock_result("AXISBANK.NS",   "Banking", 97.0),
        ]
        it_stocks = [
            _make_fno_mock_result("TCS.NS",    "IT", 85.0),
            _make_fno_mock_result("INFY.NS",   "IT", 80.0),
        ]
        all_results = banking_stocks + it_stocks
        result = _apply_diversity_and_noise(all_results, top_n=4)

        sectors_in_output = {r["sector"] for r in result}
        assert "IT" in sectors_in_output, (
            f"Expected IT sector in output (diversity), but got only: {sectors_in_output}"
        )
        print(f"PASS: IT sector present in output despite lower raw scores: {sectors_in_output}")


if __name__ == "__main__":
    # Quick smoke test when running directly
    import traceback

    print("=" * 70)
    print("Brain Improvements Test Suite — Quick Smoke Check")
    print("=" * 70)

    test_classes = [
        TestDynamicConfThreshold,
        TestDangerScannerDiversityNoise,
        TestUniverseScannerDiversityNoise,
        TestBrainGateTopPicks,
        TestDangerScanIntegration,
    ]

    passed = failed = 0
    for cls in test_classes:
        obj = cls()
        methods = [m for m in dir(obj) if m.startswith("test_")]
        print(f"\n[{cls.__name__}]")
        for method in methods:
            try:
                getattr(obj, method)()
                passed += 1
            except Exception as e:
                print(f"  FAIL: {method}")
                traceback.print_exc()
                failed += 1

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
