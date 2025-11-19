# Task 3 – GLR Pipeline (FastAPI + Vanilla Web UI)

This task replaces the Streamlit prototype with a production-friendlier split between a FastAPI backend and a lightweight HTML/CSS/JS frontend. The backend exposes a single `/api/glr` endpoint that accepts an insurance template (`.docx`) plus one or more photo report PDFs, extracts text, calls an OpenRouter LLM to determine template fields and fill them, and stores the generated `.docx` output. The frontend handles uploads, progress messaging, and shows the detected key-value pairs alongside download links.

## Features
- **FastAPI backend** that orchestrates PDF parsing (PyMuPDF), LLM calls, and Word template population (python-docx).
- **Gemini integration** via LangChain's `ChatGoogleGenerativeAI`, configurable entirely through `.env` variables.
- **Static frontend** (vanilla HTML/CSS/JS) for file uploads, status updates, result previews, and downloads.
- **Diagnostics artifacts** are written per run for auditing/debugging.
- **Unit tests** covering the docx manipulation helpers to guard against regressions in field detection logic.

## Quick Start

```bash
cd Task-3
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file inside `Task-3` with:

```
GOOGLE_API_KEY=AIza...your...key
# Optional overrides
# GEMINI_MODEL=gemini-2.5-flash
# GEMINI_TEMPERATURE=0.0
# GEMINI_MAX_OUTPUT_TOKENS=2048
```

Run tests and start the server:

```bash
pytest
uvicorn backend.main:app --reload --port 8000
```

Open the UI at `http://localhost:8000/` and upload your template + PDFs. After the pipeline finishes you'll get download and diagnostics links.

## Project Structure

```
Task-3
├── backend
│   ├── config.py
│   ├── main.py
│   ├── models.py
│   └── services
│       ├── llm_client.py
│       ├── pdf_processing.py
│       ├── pipeline.py
│       └── template_logic.py
├── static
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── task_3_output
│   └── _diagnostics
├── tests
│   └── test_template_logic.py
└── requirements.txt
```

## Notes & Future Enhancements
- Swap in a paid or custom OpenRouter model via `.env` without touching code.
- Extend the frontend to support drag-and-drop, progress bars, or authentication as needed.
- Attach Azure storage/S3 for long-term artifact retention if running in production.
