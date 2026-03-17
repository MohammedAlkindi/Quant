from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.services.trade_service import TradeService

router = APIRouter(tags=['trade'])
service = TradeService()


class TradeRequest(BaseModel):
    ticker: str
    side: str
    qty: float = Field(gt=0)
    confirmed: bool = False
    stop_loss_pct: float | None = Field(default=0.02, ge=0, le=0.2)


@router.post('/trade/execute')
def execute_trade(req: TradeRequest):
    return service.execute_trade(req.ticker.upper(), req.side, req.qty, req.confirmed, req.stop_loss_pct)


@router.get('/portfolio')
def portfolio():
    return service.get_portfolio()
