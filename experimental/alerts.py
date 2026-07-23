from pydantic import BaseModel


class AlertThresholds(BaseModel):
    z_score_threshold: float = 2.5
    sentiment_drop_threshold: float = -0.4
    confidence_floor: float = 0.55


class AnomalyAlert(BaseModel):
    ticker: str
    severity: str
    message: str
