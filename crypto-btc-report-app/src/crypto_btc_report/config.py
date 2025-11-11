from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    report_timezone: str = Field(default="Europe/Berlin", alias="REPORT_TIMEZONE")
    report_hour: int = Field(default=8, alias="REPORT_HOUR")
    coin_symbol: str = Field(default="bitcoin", alias="COIN_SYMBOL")
    vs_currency: str = Field(default="usd", alias="VS_CURRENCY")
    output_json: Path = Field(default=Path("data/latest_report.json"), alias="OUTPUT_JSON")
    output_html: Path = Field(default=Path("public/index.html"), alias="OUTPUT_HTML")
    template_path: Path = Field(default=Path("templates/report.html"), alias="TEMPLATE_PATH")
    page_word_target: int = Field(default=450, alias="PAGE_WORD_TARGET")
    articles_per_report: int = Field(default=10, alias="ARTICLES_PER_REPORT")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    rss_feeds_raw: str = Field(
        default="https://www.coindesk.com/arc/outboundfeeds/rss/,https://cointelegraph.com/rss,https://decrypt.co/feed",
        alias="RSS_FEEDS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def rss_feeds(self) -> list[str]:
        raw = self.rss_feeds_raw
        if isinstance(raw, str):
            return [item.strip() for item in raw.split(",") if item.strip()]
        if isinstance(raw, list):
            return [str(item).strip() for item in raw if str(item).strip()]
        return []


class ReportPayload(BaseModel):
    generated_at: str
    timezone: str
    coin_symbol: str
    vs_currency: str
    btc_price_summary: dict[str, Any]
    headlines: list[dict[str, Any]]
    llm_report: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
