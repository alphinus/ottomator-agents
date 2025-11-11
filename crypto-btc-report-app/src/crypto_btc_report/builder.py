from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import ReportPayload, Settings
from .news import CryptoNewsFetcher
from .price import BTCPriceFetcher
from .summarizer import ReportSummarizer


class ReportBuilder:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.news = CryptoNewsFetcher(rss_feeds=settings.rss_feeds)
        self.price = BTCPriceFetcher(
            coin_symbol=settings.coin_symbol,
            vs_currency=settings.vs_currency,
        )
        self.summarizer = ReportSummarizer(
            api_key=settings.openai_api_key or "",
            model=settings.openai_model,
            page_word_target=settings.page_word_target,
        )

    def build(self) -> ReportPayload:
        headlines = self.news.fetch_headlines(
            query="bitcoin OR crypto OR btc",
            lookback_hours=24,
            limit=self.settings.articles_per_report,
        )
        price_snapshot = self.price.fetch_last_24h()
        price_snapshot["vs_currency"] = self.settings.vs_currency

        llm_text = self.summarizer.summarize(
            headlines=headlines,
            price_snapshot=price_snapshot,
            timezone=self.settings.report_timezone,
        )

        payload = ReportPayload(
            generated_at=datetime.utcnow().isoformat() + "Z",
            timezone=self.settings.report_timezone,
            coin_symbol=self.settings.coin_symbol,
            vs_currency=self.settings.vs_currency,
            btc_price_summary=price_snapshot,
            headlines=headlines,
            llm_report=llm_text,
        )
        return payload

    def persist_json(self, payload: ReportPayload, path: Optional[Path] = None) -> Path:
        path = path or self.settings.output_json
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
        return path

    def render_html(self, payload: ReportPayload, template_path: Optional[Path] = None, output_path: Optional[Path] = None) -> Path:
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        template_path = template_path or self.settings.template_path
        output_path = output_path or self.settings.output_html

        env = Environment(
            loader=FileSystemLoader(str(template_path.parent)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template = env.get_template(template_path.name)
        html = template.render(report=payload)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
        return output_path
