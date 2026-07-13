import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { X, ArrowLeft, CaretDown, Spinner, ArrowCircleUp, ArrowCircleDown } from '@phosphor-icons/react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * Kite-style 3-column Option Chain Modal
 * Call Price | Strike Price | Put Price
 * Clicking a Call/Put row loads that option's chart
 */
const OptionChainModal = ({ symbol, name, onClose, onOptionSelect }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedExpiry, setSelectedExpiry] = useState(null);
  const [showExpiries, setShowExpiries] = useState(false);
  const atmRef = useRef(null);

  const fetchChain = async (expiry) => {
    if (!symbol) return;
    try {
      setLoading(true);
      setError(null);
      const params = expiry ? { expiry } : {};
      const res = await axios.get(`${API}/option-chain/equity/${symbol}`, { params });
      setData(res.data);
      if (!selectedExpiry && res.data?.nearest_expiry) {
        setSelectedExpiry(res.data.nearest_expiry);
      }
    } catch (e) {
      setError(e?.response?.data?.detail || 'Option chain load failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (symbol) {
      fetchChain(null);
    }
    // eslint-disable-next-line
  }, [symbol]);

  // Scroll ATM into view after data loads
  useEffect(() => {
    if (data && atmRef.current) {
      setTimeout(() => atmRef.current?.scrollIntoView({ block: 'center', behavior: 'smooth' }), 150);
    }
  }, [data]);

  const handleExpirySelect = (exp) => {
    setSelectedExpiry(exp);
    setShowExpiries(false);
    fetchChain(exp);
  };

  const handleOptionClick = (strike, side) => {
    if (!data) return;
    const expiry = selectedExpiry || data.nearest_expiry;
    const sideData = side === 'CE' ? data.chain.find(r => r.strike === strike)?.call
                                    : data.chain.find(r => r.strike === strike)?.put;
    if (!sideData) return;

    const option = {
      underlying: symbol,
      strike,
      type: side,
      expiry,
      expiry_display: expiry,
      last_price: sideData.last_price || 0,
      change_pct: sideData.change_pct || 0,
      instrument: `${symbol} ${Math.round(strike)} ${side === 'CE' ? 'Call' : 'Put'}`,
      is_live_derived: sideData.is_live_derived || data.is_live_derived || false,
      is_indicative: false,
      is_equity: true,
    };
    onOptionSelect?.(option);
  };

  const chain = data?.chain || [];
  const atmStrike = data?.atm_strike;
  const underlyingPrice = data?.underlying_price || 0;
  const maxCallOi = data?.max_call_oi || 1;
  const maxPutOi  = data?.max_put_oi  || 1;

  // Format number
  const fmt = (n) => {
    if (!n && n !== 0) return '—';
    const v = Math.abs(n);
    if (v >= 1e7) return `${(n/1e7).toFixed(1)}Cr`;
    if (v >= 1e5) return `${(n/1e5).toFixed(1)}L`;
    if (v >= 1e3) return `${(n/1e3).toFixed(1)}K`;
    return n.toLocaleString('en-IN', { maximumFractionDigits: 2 });
  };

  const fmtPct = (n) => {
    if (!n && n !== 0) return '0.00%';
    return `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`;
  };

  return (
    <div
      className="fixed inset-0 z-[120] flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={onClose}
      data-testid="option-chain-modal"
    >
      <div
        className="w-full max-w-lg bg-[#0C0C0C] border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden"
        style={{ maxHeight: '90vh', height: 640 }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-4 pt-3 pb-2 border-b border-white/10 shrink-0">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <button
                onClick={onClose}
                className="p-1 rounded-lg hover:bg-white/10 text-zinc-400 hover:text-white transition-colors"
                data-testid="option-chain-back-btn"
              >
                <ArrowLeft size={16} weight="bold" />
              </button>
              <div>
                <div className="text-sm font-black text-white uppercase tracking-wide">{name || symbol}</div>
                {underlyingPrice > 0 && (
                  <div className="text-[10px] font-mono text-zinc-400">
                    ₹{underlyingPrice.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    {data?.is_live_derived && (
                      <span className="ml-1.5 text-amber-400/80">· BS-Derived</span>
                    )}
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* Expiry selector */}
              <div className="relative">
                <button
                  onClick={() => setShowExpiries(v => !v)}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-zinc-800/80 border border-white/10 text-xs font-bold text-white hover:bg-zinc-700/80 transition-colors"
                  data-testid="expiry-selector-btn"
                >
                  {selectedExpiry || data?.nearest_expiry || 'Expiry'}
                  <CaretDown size={11} weight="bold" className={showExpiries ? 'rotate-180 transition-transform' : 'transition-transform'} />
                </button>
                {showExpiries && (data?.all_expiries?.length > 0) && (
                  <div className="absolute right-0 top-full mt-1 z-50 bg-[#1A1A1A] border border-white/10 rounded-xl shadow-2xl py-1 min-w-[140px]">
                    {data.all_expiries.map(exp => (
                      <button
                        key={exp}
                        onClick={() => handleExpirySelect(exp)}
                        className={`w-full text-left px-3 py-2 text-xs font-mono transition-colors hover:bg-white/10 ${
                          (selectedExpiry || data.nearest_expiry) === exp ? 'text-[#00E676] bg-[#00E676]/10' : 'text-zinc-300'
                        }`}
                        data-testid={`expiry-opt-${exp}`}
                      >
                        {exp}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-lg transition-colors" data-testid="option-chain-close">
                <X size={15} weight="bold" className="text-zinc-400" />
              </button>
            </div>
          </div>

          {/* Column headers */}
          <div className="grid grid-cols-5 text-[9px] font-bold uppercase tracking-wider text-zinc-500 px-1 mt-1">
            <div className="col-span-2 text-left">Call</div>
            <div className="col-span-1 text-center">Strike</div>
            <div className="col-span-2 text-right">Put</div>
          </div>
        </div>

        {/* Chain list */}
        <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-zinc-700">
          {loading && (
            <div className="py-12 flex flex-col items-center gap-2 text-zinc-500">
              <Spinner size={22} className="animate-spin" />
              <span className="text-xs">Loading option chain…</span>
            </div>
          )}

          {!loading && error && (
            <div className="py-10 text-center text-[#FF3D71] text-xs px-4">
              <div className="font-semibold mb-1">Failed to load option chain</div>
              <div className="opacity-70">{error}</div>
            </div>
          )}

          {!loading && !error && chain.length === 0 && (
            <div className="py-10 text-center text-zinc-500 text-xs">No option data found</div>
          )}

          {!loading && !error && chain.map((row) => {
            const isAtm = row.strike === atmStrike;
            const call = row.call;
            const put  = row.put;
            const callOiBars = call?.oi ? Math.max(2, Math.round((call.oi / maxCallOi) * 60)) : 0;
            const putOiBars  = put?.oi  ? Math.max(2, Math.round((put.oi  / maxPutOi)  * 60)) : 0;
            const callUp = (call?.change_pct || 0) >= 0;
            const putUp  = (put?.change_pct  || 0) >= 0;

            return (
              <div key={row.strike} ref={isAtm ? atmRef : null}>
                {/* ATM Price Banner */}
                {isAtm && underlyingPrice > 0 && (
                  <div className="mx-0 py-2 px-4 bg-zinc-800/90 border-y border-zinc-600/50 flex items-center justify-center gap-2">
                    <div className="text-xs font-bold font-mono text-white">
                      ₹{underlyingPrice.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </div>
                    <div className="text-[9px] text-zinc-400 font-mono">ATM</div>
                  </div>
                )}

                <div className={`grid grid-cols-5 items-stretch border-b transition-colors ${
                  isAtm ? 'border-zinc-600/50 bg-zinc-900/40' : 'border-white/[0.04] hover:bg-white/[0.02]'
                }`}>
                  {/* Call side (click to load CE chart) */}
                  <button
                    className="col-span-2 px-3 py-2.5 text-left flex flex-col justify-between hover:bg-[#00E676]/5 active:bg-[#00E676]/10 transition-colors"
                    onClick={() => handleOptionClick(row.strike, 'CE')}
                    data-testid={`call-row-${row.strike}`}
                    disabled={!call}
                  >
                    {call ? (
                      <>
                        <div className="text-xs font-bold font-mono text-white">
                          ₹{call.last_price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                        </div>
                        <div className={`text-[9px] font-mono font-semibold flex items-center gap-0.5 ${callUp ? 'text-[#00E676]' : 'text-[#FF3D71]'}`}>
                          {callUp ? <ArrowCircleUp size={9} weight="fill" /> : <ArrowCircleDown size={9} weight="fill" />}
                          {fmtPct(call.change_pct)}
                        </div>
                        {/* OI Bar */}
                        {callOiBars > 0 && (
                          <div className="flex justify-start mt-1">
                            <div className="h-0.5 rounded-full bg-[#00E676]/50" style={{ width: `${callOiBars}%`, maxWidth: '80%' }} />
                          </div>
                        )}
                      </>
                    ) : (
                      <span className="text-[10px] text-zinc-600">—</span>
                    )}
                  </button>

                  {/* Strike */}
                  <div className={`col-span-1 px-1 py-2.5 flex flex-col items-center justify-center ${isAtm ? 'bg-zinc-800/60' : ''}`}>
                    <div className={`text-xs font-black font-mono tabular-nums ${isAtm ? 'text-white' : 'text-zinc-300'}`}>
                      {fmt(row.strike)}
                    </div>
                    {call?.iv ? (
                      <div className="text-[8px] text-zinc-600 font-mono mt-0.5">
                        IV {call.iv.toFixed(0)}%
                      </div>
                    ) : null}
                  </div>

                  {/* Put side (click to load PE chart) */}
                  <button
                    className="col-span-2 px-3 py-2.5 text-right flex flex-col items-end justify-between hover:bg-[#FF3D71]/5 active:bg-[#FF3D71]/10 transition-colors"
                    onClick={() => handleOptionClick(row.strike, 'PE')}
                    data-testid={`put-row-${row.strike}`}
                    disabled={!put}
                  >
                    {put ? (
                      <>
                        <div className="text-xs font-bold font-mono text-white">
                          ₹{put.last_price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                        </div>
                        <div className={`text-[9px] font-mono font-semibold flex items-center gap-0.5 ${putUp ? 'text-[#00E676]' : 'text-[#FF3D71]'}`}>
                          {fmtPct(put.change_pct)}
                          {putUp ? <ArrowCircleUp size={9} weight="fill" /> : <ArrowCircleDown size={9} weight="fill" />}
                        </div>
                        {/* OI Bar */}
                        {putOiBars > 0 && (
                          <div className="flex justify-end mt-1">
                            <div className="h-0.5 rounded-full bg-[#FF3D71]/50" style={{ width: `${putOiBars}%`, maxWidth: '80%' }} />
                          </div>
                        )}
                      </>
                    ) : (
                      <span className="text-[10px] text-zinc-600">—</span>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-white/10 flex items-center justify-between shrink-0">
          <span className="text-[9px] text-zinc-600 font-mono">
            {data?.is_live_derived ? 'BS-Derived · Click row to load chart' : 'NSE Live · Click row to load chart'}
          </span>
          <button
            onClick={() => fetchChain(selectedExpiry)}
            className="text-[9px] text-zinc-500 hover:text-white font-bold uppercase tracking-wider transition-colors px-2 py-1 rounded hover:bg-white/10"
            data-testid="option-chain-refresh"
          >
            Refresh
          </button>
        </div>
      </div>
    </div>
  );
};

export default OptionChainModal;
