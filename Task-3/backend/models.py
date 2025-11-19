from __future__ import annotations

from typing import Dict

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str


class PipelineSuccessResponse(BaseModel):
    run_id: str
    download_url: str
    pdf_url: str | None = None
    diagnostics_url: str
    extracted_fields: Dict[str, str]
    filled_values: Dict[str, str]
    report_excerpt: str


class ErrorResponse(BaseModel):
    detail: str
