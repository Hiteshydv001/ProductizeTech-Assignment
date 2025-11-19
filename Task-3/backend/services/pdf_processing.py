from __future__ import annotations

from io import BytesIO
from typing import Iterable

import fitz  # type: ignore


def extract_text_from_pdfs(pdf_streams: Iterable[bytes]) -> str:
    combined_text: list[str] = []
    for index, content in enumerate(pdf_streams):
        if not content:
            continue
        with fitz.open(stream=BytesIO(content), filetype="pdf") as doc:
            for page in doc:
                combined_text.append(page.get_text())
        combined_text.append(f"\n--- End of Report {index + 1} ---\n")
    return "\n".join(combined_text).strip()
