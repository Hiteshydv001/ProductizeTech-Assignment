from __future__ import annotations

import base64
import uuid
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from task_2_code import annotate_changes

app = FastAPI(title="Visual Change Detector")

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "task_2_output"
TEMPLATE_DIR = BASE_DIR / "templates"

OUTPUT_DIR.mkdir(exist_ok=True)
TEMPLATE_DIR.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


def _image_from_upload(data: bytes, filename: str) -> np.ndarray:
    array = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail=f"Unable to decode image data from {filename}.")
    return image


def _encode_image(image: np.ndarray) -> str:
    success, buffer = cv2.imencode(".png", image)
    if not success:
        raise ValueError("Unable to encode image for preview.")
    return base64.b64encode(buffer).decode("utf-8")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    context = {
        "request": request,
        "image_data": None,
        "download_url": None,
        "message": None,
        "before_data": None,
        "after_data": None,
    }
    return templates.TemplateResponse("index.html", context)


@app.post("/process", response_class=HTMLResponse)
async def process_images(
    request: Request,
    before_image: UploadFile = File(...),
    after_image: UploadFile = File(...),
) -> HTMLResponse:
    before_b64: str | None = None
    after_b64: str | None = None
    try:
        before_bytes = await before_image.read()
        after_bytes = await after_image.read()
        before = _image_from_upload(before_bytes, before_image.filename or "before image")
        after = _image_from_upload(after_bytes, after_image.filename or "after image")
        before_b64 = _encode_image(before)
        after_b64 = _encode_image(after)
        annotated = annotate_changes(before, after)
        annotated_b64 = _encode_image(annotated)
    except ValueError as exc:
        context = {
            "request": request,
            "image_data": None,
            "download_url": None,
            "message": str(exc),
            "before_data": before_b64,
            "after_data": after_b64,
        }
        return templates.TemplateResponse("index.html", context, status_code=400)

    output_name = f"changes_{uuid.uuid4().hex}.png"
    output_path = OUTPUT_DIR / output_name
    cv2.imwrite(str(output_path), annotated)

    context = {
        "request": request,
        "image_data": annotated_b64,
        "download_url": f"/download/{output_name}",
        "message": "Processing complete. Preview below.",
        "before_data": before_b64,
        "after_data": after_b64,
    }
    return templates.TemplateResponse("index.html", context)


@app.get("/download/{filename}")
async def download_image(filename: str) -> FileResponse:
    target = OUTPUT_DIR / filename
    if not target.exists():
        raise HTTPException(status_code=404, detail="Requested file not found.")
    return FileResponse(target, media_type="image/png", filename=filename)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
