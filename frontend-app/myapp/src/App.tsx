import { useEffect, useMemo, useState } from 'react'
import './App.css'
import TradingAppLogo from './assets/TradingAppLogo.png'

// Configure your API base URL in .env.local as VITE_API_URL=http://localhost:8000
const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// ---- Types matching the FastAPI scaffold ----
export type AccountBalance = {
  currency: string
  cash: number
  equity: number
  buying_power: number
  timestamp: string
}

export type Position = {
  symbol: string
  qty: number
  avg_price: number
  side: 'LONG' | 'SHORT'
}

export type Order = {
  id: string
  symbol: string
  side: 'BUY' | 'SELL'
  qty: number
  order_type: 'MARKET' | 'LIMIT'
  limit_price?: number | null
  tif: 'DAY' | 'GTC'
  status: 'NEW' | 'PARTIALLY_FILLED' | 'FILLED' | 'CANCELED' | 'REJECTED'
  created_at: string
  avg_fill_price?: number | null
  filled_qty: number
}

export type TradeStats = {
  symbol: string
  window: string
  trades: number
  win_rate: number // 0..1
  pnl: number
  avg_return: number // 0..1 per trade
  sharpe?: number | null
  last_updated: string
}

function App() {
  const [count, setCount] = useState(0)

  // Dashboard state
  const [balance, setBalance] = useState<AccountBalance | null>(null)
  const [positions, setPositions] = useState<Position[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [stats, setStats] = useState<TradeStats | null>(null)

  const [symbol, setSymbol] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const currency = balance?.currency ?? 'USD'
  const fmtMoney = (n: number) =>
    n.toLocaleString(undefined, { style: 'currency', currency })
  const fmtPct = (x: number) => `${(x * 100).toFixed(2)}%`

  async function fetchJSON<T>(url: string): Promise<T> {
    const res = await fetch(url)
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
    return res.json()
  }

  const loadAll = async () => {
    setLoading(true)
    setError(null)
    try {
      const [b, p, o, s] = await Promise.all([
        fetchJSON<AccountBalance>(`${API_BASE}/api/v1/account/balance`),
        fetchJSON<Position[]>(`${API_BASE}/api/v1/positions/open`),
        fetchJSON<Order[]>(`${API_BASE}/api/v1/orders/open`),
        fetchJSON<TradeStats>(
          `${API_BASE}/api/v1/trades/stats?symbol=${encodeURIComponent(symbol)}&window=30d`
        ),
      ])
      setBalance(b)
      setPositions(p)
      setOrders(o)
      setStats(s)
    } catch (e: any) {
      setError(e?.message ?? 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // initial load
    loadAll()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    // refresh stats when symbol changes
    ;(async () => {
      try {
        const s = await fetchJSON<TradeStats>(
          `${API_BASE}/api/v1/trades/stats?symbol=${encodeURIComponent(symbol)}&window=30d`
        )
        setStats(s)
      } catch (e) {
        // ignore here, user might be typing
      }
    })()
  }, [symbol])

  const equityDelta = useMemo(() => {
    if (!balance) return null
    return balance.equity - balance.cash
  }, [balance])

  return (
    <>
      {/* Header */}
      <div className="header">
        <img src={TradingAppLogo} className="logo" alt="Trading App logo" />
        <div>
          <h2>Kalshi Trading Application</h2>
        </div>
      </div>

      {/* Controls */}
      <div className="toolbar">
        <div className="right">
          <label htmlFor="symbol">Search Markets:&nbsp;</label>
          <input
            id="symbol"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            className="input"
            
          />
          <button className="btn" onClick={loadAll} disabled={loading}>
            {loading ? 'Loading…' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div className="alert error">⚠️ {error}</div>
      )}

      {/* Cards Grid */}
      <div className="grid">
        {/* Account Value */}
        <section className="card">
          <h3>Account Value</h3>
          {!balance ? (
            <p className="muted">Loading…</p>
          ) : (
            <ul className="kv">
              <li>
                <span>Cash</span>
                <strong>{fmtMoney(balance.cash)}</strong>
              </li>
              <li>
                <span>Equity</span>
                <strong>{fmtMoney(balance.equity)}</strong>
              </li>
              <li>
                <span>Buying Power</span>
                <strong>{fmtMoney(balance.buying_power)}</strong>
              </li>
              {equityDelta !== null && (
                <li>
                  <span>Unrealized Δ</span>
                  <strong className={equityDelta >= 0 ? 'pos' : 'neg'}>
                    {fmtMoney(equityDelta)}
                  </strong>
                </li>
              )}
            </ul>
          )}
        </section>

        {/* Open Positions */}
        <section className="card">
          <h3>Open Positions</h3>
          {positions.length === 0 ? (
            <p className="muted">No open positions</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Side</th>
                  <th>Qty</th>
                  <th>Avg Price</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((p) => (
                  <tr key={p.symbol}>
                    <td>{p.symbol}</td>
                    <td>
                      <span className={`pill ${p.side === 'LONG' ? 'pos' : 'neg'}`}>
                        {p.side}
                      </span>
                    </td>
                    <td>{p.qty}</td>
                    <td>{fmtMoney(p.avg_price)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        {/* Statistics */}
        <section className="card">
          <h3>Statistics ({symbol})</h3>
          {!stats ? (
            <p className="muted">Loading…</p>
          ) : (
            <ul className="kv">
              <li>
                <span>Trades</span>
                <strong>{stats.trades}</strong>
              </li>
              <li>
                <span>Win rate</span>
                <strong>{fmtPct(stats.win_rate)}</strong>
              </li>
              <li>
                <span>Total PnL</span>
                <strong className={stats.pnl >= 0 ? 'pos' : 'neg'}>
                  {fmtMoney(stats.pnl)}
                </strong>
              </li>
              <li>
                <span>Avg Return / trade</span>
                <strong className={stats.avg_return >= 0 ? 'pos' : 'neg'}>
                  {fmtPct(stats.avg_return)}
                </strong>
              </li>
              {typeof stats.sharpe === 'number' && (
                <li>
                  <span>Sharpe</span>
                  <strong>{stats.sharpe?.toFixed(2)}</strong>
                </li>
              )}
            </ul>
          )}
        </section>

        {/* Orders */}
        <section className="card">
          <h3>Orders</h3>
          {orders.length === 0 ? (
            <p className="muted">No open orders</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Side</th>
                  <th>Qty</th>
                  <th>Type</th>
                  <th>Limit</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => (
                  <tr key={o.id}>
                    <td>{o.symbol}</td>
                    <td>{o.side}</td>
                    <td>{o.qty}</td>
                    <td>{o.order_type}</td>
                    <td>{o.limit_price ? fmtMoney(o.limit_price) : '—'}</td>
                    <td>
                      <span className={`pill status-${o.status.toLowerCase()}`}>
                        {o.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>

      {/* Demo counter (keep the Vite starter feel) */}
      <div className="card center">
        <button onClick={() => setCount((c) => c + 1)}>count is {count}</button>
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
      </div>

      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  )
}

export default App
