from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes_llm import router as llm_router
from backend.api.routes_market import router as market_router
from backend.api.routes_signal import router as signal_router
from backend.api.routes_trade import router as trade_router
from backend.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, version='0.1.0', debug=settings.debug)

origins = [o.strip() for o in settings.cors_origins.split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(market_router, prefix=settings.api_prefix)
app.include_router(signal_router, prefix=settings.api_prefix)
app.include_router(trade_router, prefix=settings.api_prefix)
app.include_router(llm_router, prefix=settings.api_prefix)


@app.get('/healthz')
def healthcheck() -> dict[str, str]:
    return {'status': 'ok'}
