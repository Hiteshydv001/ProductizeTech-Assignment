# Task 2 · Visual Change Detector

Task 2 highlights the differences between an "original" image and its edited counterpart by drawing bounding boxes around changed regions. The project ships with both a command-line batch processor and a FastAPI-powered web interface that previews uploads and results in a monochrome theme.

## Requirements

Install dependencies into your active virtual environment:

```powershell
pip install -r requirements.txt
```

## Command-Line Usage

1. Place paired images inside `input-images/`. Each pair should follow the convention:
   - `scene.jpg` (original frame)
   - `scene~2.jpg` (edited frame with objects added/removed)
2. Run the script:

```powershell
python task_2_code.py
```

Outputs are written to `task_2_output/scene~3.jpg` with change regions boxed in red. Missing counterpart images are reported in the console.

## Web Interface (FastAPI)

1. Stay inside the `Task-2` folder and ensure the virtual environment is active.
2. Launch the server:

```powershell
uvicorn app:app --reload
```

3. Open `http://127.0.0.1:8000/` in your browser.
4. Upload the original image and the edited image. The UI will render:
   - Original upload preview
   - Edited upload preview
   - Processed result with highlighted changes and a download button
5. Click **Download Result** to save the annotated PNG.

Stop the server with `Ctrl+C` when finished.

## How It Works

- `task_2_code.py` exposes `annotate_changes(before, after)` to detect differences with grayscale subtraction, thresholding, dilation, and contour bounding boxes.
- `app.py` serves the FastAPI application, reusing `annotate_changes` to process user uploads and returning previews via base64 data URIs.
- `templates/index.html` implements a black-and-white responsive layout with the dual-upload form and preview panels.

## Notes

- Ensure uploaded images share the same resolution and color channels to avoid processing errors.
- Output files are stored in `task_2_output/`; the directory is created automatically if it does not exist.
- For production use, disable `--reload` and run behind a production-grade ASGI server.
