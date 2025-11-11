from __future__ import annotations

from typing import Any, Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - offline fallback
    OpenAI = None  # type: ignore


class SummarizationError(RuntimeError):
    pass


class ReportSummarizer:
    """Generates the daily brief via OpenAI if possible, otherwise a deterministic fallback."""

    def __init__(self, api_key: Optional[str], model: str = "gpt-4o-mini", page_word_target: int = 450) -> None:
        self.model = model
        self.page_word_target = page_word_target
        self.api_key = api_key
        self.client = None
        if api_key and OpenAI is not None:
            self.client = OpenAI(api_key=api_key)

    def summarize(
        self,
        headlines: list[dict[str, Any]],
        price_snapshot: dict[str, Any],
        timezone: str,
    ) -> str:
        bullet_lines = [
            f"- {item.get('title')} ({item.get('source')}) -> {item.get('url')}"
            for item in headlines
        ]
        price_line = (
            f"BTC price current {price_snapshot['current_price']:.2f} {price_snapshot['vs_currency'].upper() if 'vs_currency' in price_snapshot else 'USD'}, "
            f"24h change {price_snapshot['change_percentage']:.2f}% (high {price_snapshot['high']:.2f}, low {price_snapshot['low']:.2f})."
        )
        if not self.client:
            return self._local_summary(price_line, bullet_lines)
        system_prompt = (
            "You are a financial research analyst tasked with preparing a crisp, one-page A4 report "
            "focused on the cryptocurrency market with emphasis on Bitcoin. Limit the report to "
            f"approximately {self.page_word_target} words, organize it into brief sections "
            "('Market Snapshot', 'Key Headlines', 'Opportunities & Risks', 'Watchlist'). "
            "Cite sources inline using [#] referencing order of the supplied articles."
        )
        user_prompt = "\n".join(
            [
                f"Timezone for timestamps: {timezone}",
                price_line,
                "Headlines:",
                *bullet_lines,
            ]
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.4,
                max_tokens=900,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:  # noqa: BLE001
            raise SummarizationError(f"OpenAI summarization failed: {exc}") from exc

        message = response.choices[0].message.content if response.choices else ""
        return (message or "").strip()

    def _local_summary(self, price_line: str, bullet_lines: list[str]) -> str:
        """Fallback deterministic summary so devs can test without LLM creds."""
        sections = [
            "# Market Snapshot\n" + price_line,
            "# Key Headlines\n" + "\n".join(bullet_lines[:5]),
            "# Opportunities & Risks\n" + "\n".join(
                [
                    "- Opportunity: Monitor institutional flows if momentum stays positive.",
                    "- Risk: Macro surprise or ETF outflows could spike volatility.",
                ]
            ),
            "# Watchlist\n" + "\n".join(
                [
                    "- Funding rates and perp OI",
                    "- BTC dominance vs ETH/BTC",
                    "- Stablecoin net issued",
                ]
            ),
            "\n(Offline mode: set OPENAI_API_KEY for richer narrative.)",
        ]
        return "\n\n".join(sections)
