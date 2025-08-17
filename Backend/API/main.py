# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uuid

app = FastAPI(title="Algo Trading API", version="0.1.0")

# Allow your Vite dev server(s)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_origin_regex=r"https://.*\.trycloudflare\.com",
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Models ----------
class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class TimeInForce(str, Enum):
    DAY = "DAY"
    GTC = "GTC"

class AccountBalance(BaseModel):
    currency: str = "USD"
    cash: float = 0.0
    equity: float = 0.0
    buying_power: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Position(BaseModel):
    symbol: str
    qty: float
    avg_price: float
    side: str  # "LONG" or "SHORT"

class OrderRequest(BaseModel):
    symbol: str
    side: Side
    qty: float = Field(gt=0)
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = Field(default=None, gt=0)
    tif: TimeInForce = TimeInForce.DAY
    client_order_id: Optional[str] = None  # for idempotency

class Order(BaseModel):
    id: str
    symbol: str
    side: Side
    qty: float
    order_type: OrderType
    limit_price: Optional[float]
    tif: TimeInForce
    status: str  # "NEW" | "PARTIALLY_FILLED" | "FILLED" | "CANCELED" | "REJECTED"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    avg_fill_price: Optional[float] = None
    filled_qty: float = 0.0

class TradeStats(BaseModel):
    symbol: str
    window: str
    trades: int
    win_rate: float
    pnl: float
    avg_return: float
    sharpe: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

STATE = {
    "balance": AccountBalance(currency="USD", cash=100001.0, equity=100000.0, buying_power=200000.0),
    "positions": [
        Position(symbol="AAPL", qty=50, avg_price=190.0, side="LONG"),
        Position(symbol="TSLA", qty=10, avg_price=240.0, side="SHORT"),
    ],
    "orders": {},
}

@app.get("/api/v1/account/balance", response_model=AccountBalance, tags=["Account"])
def get_balance():
    # TODO: fetch from broker API (e.g., Alpaca/IBKR/TD)
    STATE["balance"].timestamp = datetime.utcnow()
    return STATE["balance"]

@app.get("/api/v1/positions/open", response_model=List[Position], tags=["Positions"])
def get_open_positions():
    # TODO: fetch open positions from broker
    return STATE["positions"]

@app.get("/api/v1/orders/open", response_model=List[Order], tags=["Orders"])
def get_open_orders():
    # Filter unfilled/active orders
    return [o for o in STATE["orders"].values() if o.status in {"NEW", "PARTIALLY_FILLED"}]

@app.post("/api/v1/orders", response_model=Order, tags=["Orders"], status_code=201)
def place_order(req: OrderRequest):

    if req.order_type == OrderType.LIMIT and req.limit_price is None:
        raise HTTPException(status_code=400, detail="limit_price required for LIMIT orders")

    for o in STATE["orders"].values():
        if req.client_order_id and o.id == req.client_order_id:
            return o

    order_id = req.client_order_id or str(uuid.uuid4())
    order = Order(
        id=order_id,
        symbol=req.symbol.upper(),
        side=req.side,
        qty=req.qty,
        order_type=req.order_type,
        limit_price=req.limit_price,
        tif=req.tif,
        status="NEW",
    )
    STATE["orders"][order.id] = order

    # TODO: send to broker API here; handle async fills via webhook/cron/WebSocket
    return order

@app.get("/api/v1/orders/{order_id}", response_model=Order, tags=["Orders"])
def get_order(order_id: str):
    order = STATE["orders"].get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/v1/trades/stats", response_model=TradeStats, tags=["Analytics"])
def get_trade_stats(symbol: str, window: str = "30d"):
    # TODO: compute from your fills/trade history store
    # Parse window quickly
    now = datetime.utcnow()
    try:
        if window.endswith("d"):
            _days = int(window[:-1])
            start = now - timedelta(days=_days)
        elif window.endswith("h"):
            _hrs = int(window[:-1])
            start = now - timedelta(hours=_hrs)
        else:
            raise ValueError
    except Exception:
        raise HTTPException(status_code=400, detail="window must be like '7d' or '12h'")

    return TradeStats(
        symbol=symbol.upper(),
        window=window,
        trades=42,
        win_rate=0.57,
        pnl=1234.56,
        avg_return=0.0123,
        sharpe=1.4,
        last_updated=now,
    )
BASE_DIR = Path(__file__).resolve().parents[2]  # -> KalshiTradingApplication/
DIST_DIR = BASE_DIR / "frontend-app" / "myapp" / "dist"
#
app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="spa")