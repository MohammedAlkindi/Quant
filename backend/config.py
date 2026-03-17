from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Quant API'
    api_prefix: str = '/api'
    debug: bool = False

    postgres_url: str = Field(..., alias='POSTGRES_URL')
    redis_url: str = Field(..., alias='REDIS_URL')

    polygon_api_key: str = Field('', alias='POLYGON_API_KEY')
    alpha_vantage_api_key: str = Field('', alias='ALPHA_VANTAGE_API_KEY')
    alpaca_api_key: str = Field('', alias='ALPACA_API_KEY')
    alpaca_secret_key: str = Field('', alias='ALPACA_SECRET_KEY')
    alpaca_base_url: str = Field('https://paper-api.alpaca.markets', alias='ALPACA_BASE_URL')
    anthropic_api_key: str = Field('', alias='ANTHROPIC_API_KEY')
    claude_model: str = Field('claude-sonnet-4-20250514', alias='CLAUDE_MODEL')

    cors_origins: str = Field('http://localhost:5173,http://localhost:3000', alias='CORS_ORIGINS')

    default_tickers: str = Field('AAPL,MSFT,NVDA,TSLA,SPY', alias='DEFAULT_TICKERS')


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
