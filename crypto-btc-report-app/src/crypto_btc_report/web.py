from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from pydantic import ValidationError

from .config import ReportPayload, get_settings

settings = get_settings()
app = FastAPI(title="Crypto BTC Daily Report")


def _load_payload(path: Path) -> ReportPayload:
    if not path.exists():
        raise FileNotFoundError(f"Report file {path} not found. Generate it first.")
    try:
        return ReportPayload.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        raise FileNotFoundError("Report file exists but is not populated yet.") from exc


@app.get("/api/report", response_model=ReportPayload)
def get_report() -> ReportPayload:
    try:
        return _load_payload(settings.output_json)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/", response_class=HTMLResponse)
def serve_report() -> HTMLResponse:
    html_path = settings.output_html
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Report not generated yet.")
    return HTMLResponse(html_path.read_text(encoding="utf-8"))
