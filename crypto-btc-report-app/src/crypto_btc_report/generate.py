from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console

from .builder import ReportBuilder
from .config import get_settings

console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate BTC daily report")
    parser.add_argument("--output-json", type=Path, help="Override JSON output path")
    parser.add_argument("--output-html", type=Path, help="Override HTML output path")
    parser.add_argument("--template", type=Path, help="Override template path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    if args.output_json:
        settings.output_json = args.output_json
    if args.output_html:
        settings.output_html = args.output_html
    if args.template:
        settings.template_path = args.template

    console.log("Generating crypto report...")
    builder = ReportBuilder(settings)
    payload = builder.build()
    json_path = builder.persist_json(payload)
    html_path = builder.render_html(payload)
    console.log(f"Report saved to {json_path} and {html_path}")


if __name__ == "__main__":
    main()
