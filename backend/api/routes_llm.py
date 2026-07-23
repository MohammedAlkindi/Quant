from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.llm_service import LLMService

router = APIRouter(tags=['llm'])
service = LLMService()


class AnalyzeRequest(BaseModel):
    ticker: str
    momentum_projection: float
    rl_action: str
    anomaly_flags: dict
    sentiment_score: float


@router.post('/analyze')
def analyze(req: AnalyzeRequest):
    return service.analyze_signal(req.model_dump())


class ExplainRequest(BaseModel):
    context: dict


@router.post('/explain')
def explain(req: ExplainRequest):
    return service.analyze_signal(req.context)
