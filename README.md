# ProductizeTech Assignment

This repository contains three focused tasks that together demonstrate computer-vision alignment, visual diffing, and document automation with an LLM-backed pipeline. Each task is self-contained with its own inputs, outputs, and entry points, but they share common Python tooling practices such as virtual environments and requirements files.

## Task 1 · Thermal/RGB Alignment
- **Goal:** Align drone-captured RGB and thermal images so that corresponding pixels line up for downstream analysis.
- **Approach:**
  - Run `calibrate_manual.py` once to select corresponding points between a representative RGB/thermal pair. The script rescales the thermal frame to the RGB height, collects four matching points, and fits an affine transform that preserves parallel lines (suitable for aerial imagery).
  - Persist the calibration matrix and scale factor to `calibration_matrix.npy` for reuse.
  - Execute `task_1_code.py` to batch-process every `_Z.JPG` RGB image by resizing the paired thermal frame with the stored scale factor, warping it with the affine transform, and exporting aligned `_AT.JPG` results alongside the original RGBs.
  - If no calibration exists, the code falls back to a centered resize so you still get outputs, though the alignment quality is reduced.
- **Run:**
  ```powershell
  cd Task-1
  python -m venv venv
  .\venv\Scripts\activate
  pip install opencv-python numpy
  python calibrate_manual.py
  python task_1_code.py
  ```

## Task 2 · Visual Change Detector
- **Goal:** Spot visual edits between an "original" and an "edited" image by highlighting modified regions.
- **Approach:**
  - `task_2_code.py` pairs files that follow the `scene.jpg` / `scene~2.jpg` naming convention, converts them to grayscale, computes the absolute difference, thresholds the result, dilates to merge nearby pixels, and draws red bounding boxes around the detected contours before writing annotated outputs to `task_2_output/`.
  - `app.py` exposes the same pipeline through a FastAPI server and serves a monochrome single-page interface (`templates/index.html`) that previews uploads and results with a download button.
- **Run (CLI):**
  ```powershell
  cd Task-2
  python -m venv venv
  .\venv\Scripts\activate
  pip install -r requirements.txt
  python task_2_code.py
  ```
- **Run (Web):**
  ```powershell
  cd Task-2
  .\venv\Scripts\activate
  uvicorn app:app --reload
  ```
  Navigate to `http://127.0.0.1:8000/` and upload an original/edited pair.

## Task 3 · GLR Automation Pipeline
- **Goal:** Convert the Streamlit proof-of-concept into a production-style stack that reads insurance PDFs, extracts structured data, and fills a Word template via LLM-assisted reasoning.
- **Approach:**
  - `backend/main.py` exposes a FastAPI `/api/glr` endpoint that accepts a `.docx` template plus one or more PDF photo reports.
  - The pipeline in `services/` orchestrates PDF text extraction (PyMuPDF), prompt assembly, a LangChain-powered Gemini call (using credentials from `.env`), and document population via python-docx.
  - Results—completed templates, detected key-value pairs, and diagnostics JSON—are saved under `task_3_output/` for auditing. Unit tests in `tests/` guard critical template logic.
  - A static frontend in `static/` handles uploads, progress messaging, and download links, keeping deployment lightweight.
- **Run:**
  ```powershell
  cd Task-3
  python -m venv .venv
  .\.venv\Scripts\activate
  pip install -r requirements.txt
  # Create a .env with GOOGLE_API_KEY and optional overrides before running
  pytest
  uvicorn backend.main:app --reload --port 8000
  ```
  Visit `http://localhost:8000/` to access the UI.

## Common Notes
- Python 3.10+ is recommended across all tasks.
- Input and output folders are pre-created; ensure sample files follow the documented naming conventions.
- Deactivate the virtual environment with `deactivate` when finished.
