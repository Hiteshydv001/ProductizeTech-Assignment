from __future__ import annotations

import json
import uuid
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from backend.config import DIAGNOSTICS_DIR, OUTPUT_DIR, get_settings
from backend.services.llm_client import create_chat_completion
from backend.services.pdf_processing import extract_text_from_pdfs
from backend.services.template_logic import detect_fields_with_llm, fill_template


@dataclass
class PipelineResult:
    run_id: str
    download_path: Path
    diagnostics_path: Path
    extracted_fields: Dict[str, str]
    filled_values: Dict[str, str]
    report_excerpt: str


class GLRPipeline:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _extract_data_with_llm(self, report_text: str, fields_to_fill: Dict[str, str]) -> Dict[str, str]:
        # Truncate report text to avoid overwhelming the model
        truncated_text = report_text[:self.settings.max_report_chars]
        if len(report_text) > self.settings.max_report_chars:
            print(f"[pipeline] Report truncated from {len(report_text)} to {self.settings.max_report_chars} chars")
        
        prompt = f"""Extract information from this insurance report and fill the JSON template with complete, detailed information.

CRITICAL EXTRACTION RULES:
1. Extract COMPLETE information - don't summarize or truncate
2. Copy multi-line descriptions EXACTLY as written, preserving ALL details
3. For dates like "Date of Loss: 9/28/2024", extract "9/28/2024"
4. For descriptive fields (e.g., "Dwelling Description", "Roof Description"), extract the ENTIRE description verbatim
5. Include ALL measurements, materials, observations, and technical details
6. If field says "N/A" or "None", copy that exact text
7. Leave empty ("") only if truly missing from the report
8. Preserve original formatting, punctuation, and paragraph structure
9. Do NOT paraphrase or shorten any text - copy it word-for-word

REPORT TEXT ({len(truncated_text)} chars):
{truncated_text}

FIELDS TO FILL:
{json.dumps(fields_to_fill, indent=2)}

Return ONLY the filled JSON with complete extracted values, no markdown or commentary.
Include ALL available details from the report."""

        response = create_chat_completion(
            messages=[
                {"role": "system", "content": "You are a precise data extraction assistant. Extract complete, verbatim information from insurance documents into JSON format. Never summarize or truncate - copy all details exactly as written."},
                {"role": "user", "content": prompt},
            ]
        )
        try:
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            print(f"[pipeline] Failed to parse LLM response as JSON: {response[:500]}")
            raise ValueError("LLM failed to return valid JSON for report extraction") from exc

    def run(self, template_bytes: bytes, pdf_payloads: List[bytes]) -> PipelineResult:
        if not template_bytes:
            raise ValueError("Template file is empty")
        if not pdf_payloads:
            raise ValueError("At least one PDF report is required")

        report_text = extract_text_from_pdfs(pdf_payloads)
        if not report_text:
            raise ValueError("Could not extract any text from the provided PDF reports")

        fields = detect_fields_with_llm(template_bytes)
        if not fields:
            raise ValueError("No fields detected inside the template")

        filled_values = self._extract_data_with_llm(report_text, fields)
        filled_doc_bytes = fill_template(template_bytes, filled_values)

        unique_id = uuid.uuid4().hex
        output_docx_path = OUTPUT_DIR / f"filled_template_{unique_id}.docx"
        output_pdf_path = OUTPUT_DIR / f"filled_template_{unique_id}.pdf"
        diagnostics_path = DIAGNOSTICS_DIR / f"pipeline_run_{unique_id}.json"

        # Save DOCX
        output_docx_path.write_bytes(filled_doc_bytes)

        # Try to convert to PDF
        pdf_generated = False
        try:
            # Try docx2pdf (Windows only, requires Word)
            from docx2pdf import convert
            convert(str(output_docx_path), str(output_pdf_path))
            pdf_generated = True
            print(f"[pipeline] PDF generated using docx2pdf: {output_pdf_path}")
        except Exception as e:
            print(f"[pipeline] docx2pdf failed: {e}")
            # Try LibreOffice as fallback
            try:
                subprocess.run(
                    [
                        "soffice",
                        "--headless",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        str(OUTPUT_DIR),
                        str(output_docx_path),
                    ],
                    check=True,
                    capture_output=True,
                    timeout=30,
                )
                temp_pdf = output_docx_path.with_suffix(".pdf")
                if temp_pdf.exists():
                    if temp_pdf != output_pdf_path:
                        temp_pdf.rename(output_pdf_path)
                    pdf_generated = True
                    print(f"[pipeline] PDF generated using LibreOffice: {output_pdf_path}")
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e2:
                print(f"[pipeline] Warning: Could not convert to PDF (neither Word nor LibreOffice available)")
                print("[pipeline] Install Microsoft Word or LibreOffice for PDF export")

        diagnostics_path.write_text(
            json.dumps(
                {
                    "fields": fields,
                    "filled_values": filled_values,
                    "report_excerpt": report_text[:5000],
                    "docx_path": str(output_docx_path),
                    "pdf_path": str(output_pdf_path) if pdf_generated else None,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        return PipelineResult(
            run_id=unique_id,
            download_path=output_docx_path,
            diagnostics_path=diagnostics_path,
            extracted_fields=fields,
            filled_values=filled_values,
            report_excerpt=report_text[:4000],
        )
