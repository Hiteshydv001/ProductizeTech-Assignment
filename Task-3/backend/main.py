from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.config import DIAGNOSTICS_DIR, OUTPUT_DIR, ROOT_DIR
from backend.models import ErrorResponse, HealthResponse, PipelineSuccessResponse
from backend.services.pipeline import GLRPipeline

app = FastAPI(title="GLR Insurance Pipeline", version="0.1.0")
pipeline = GLRPipeline()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = ROOT_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
def serve_frontend() -> HTMLResponse:
    index_path = static_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not built yet")
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok", version=app.version)


@app.post("/api/glr", response_model=PipelineSuccessResponse, responses={400: {"model": ErrorResponse}})
async def run_pipeline(
    template: UploadFile = File(..., description="Insurance template in .docx format"),
    reports: List[UploadFile] = File(..., description="One or more photo reports in .pdf format"),
) -> PipelineSuccessResponse:
    if template.content_type not in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"):
        raise HTTPException(status_code=400, detail="Template must be a .docx file")
    if not reports:
        raise HTTPException(status_code=400, detail="Provide at least one PDF report")

    template_bytes = await template.read()
    pdf_payloads = []
    for upload in reports:
        if upload.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail=f"{upload.filename} is not a PDF")
        pdf_payloads.append(await upload.read())

    try:
        result = pipeline.run(template_bytes, pdf_payloads)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    download_url = f"/api/download/{result.run_id}"
    pdf_url = f"/api/download-pdf/{result.run_id}"
    diagnostics_url = f"/api/diagnostics/{result.run_id}"
    
    # Check if PDF was actually generated
    pdf_path = OUTPUT_DIR / f"filled_template_{result.run_id}.pdf"
    if not pdf_path.exists():
        pdf_url = None

    return PipelineSuccessResponse(
        run_id=result.run_id,
        download_url=download_url,
        pdf_url=pdf_url,
        diagnostics_url=diagnostics_url,
        extracted_fields=result.extracted_fields,
        filled_values=result.filled_values,
        report_excerpt=result.report_excerpt,
    )


@app.get("/api/download/{run_id}")
def download_document(run_id: str) -> FileResponse:
    file_path = OUTPUT_DIR / f"filled_template_{run_id}.docx"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(file_path, filename=file_path.name)


@app.get("/api/download-pdf/{run_id}")
def download_pdf(run_id: str) -> FileResponse:
    file_path = OUTPUT_DIR / f"filled_template_{run_id}.pdf"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found. LibreOffice may not be installed.")
    return FileResponse(file_path, filename=file_path.name, media_type="application/pdf")


@app.get("/api/diagnostics/{run_id}")
def fetch_diagnostics(run_id: str) -> FileResponse:
    diag_path = DIAGNOSTICS_DIR / f"pipeline_run_{run_id}.json"
    if not diag_path.exists():
        raise HTTPException(status_code=404, detail="Diagnostics not found")
    return FileResponse(diag_path, filename=diag_path.name)
