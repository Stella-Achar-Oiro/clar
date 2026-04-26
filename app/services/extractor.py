from pathlib import Path

import pdfplumber

_REPORT_TYPE_KEYWORDS: dict[str, list[str]] = {
    "radiology": [
        "radiology", "x-ray", "xray", "mri", "ct scan",
        "ultrasound", "imaging", "findings:", "impression:",
    ],
    "pathology": [
        "pathology", "biopsy", "histology", "specimen",
        "microscopic", "gross description",
    ],
    "discharge": [
        "discharge summary", "discharged", "admission date",
        "discharge date", "discharge diagnosis",
    ],
    "lab": [
        "cbc", "blood panel", "haemoglobin", "hemoglobin",
        "glucose", "creatinine", "laboratory", "lab results",
    ],
}


def extract_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.suffix.lower() == ".pdf":
        return _extract_pdf(path)
    return path.read_text(encoding="utf-8")


def _extract_pdf(path: Path) -> str:
    pages: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            parts: list[str] = []

            # Extract tables as pipe-separated rows to preserve column structure.
            # Plain extract_text() collapses table columns into garbled runs.
            for table in page.extract_tables():
                for row in table:
                    cells = [c.replace("\n", " ").strip() if c else "" for c in row]
                    if any(cells):
                        parts.append(" | ".join(cells))

            # Fall back to free-text extraction for pages with no tables
            # (e.g. radiology impressions, narrative discharge summaries).
            if not parts:
                text = page.extract_text()
                if text:
                    parts.append(text)

            if parts:
                pages.append("\n".join(parts))

    if not pages:
        raise ValueError(
            "PDF contains no extractable text — may be a scanned image."
            " Only digital PDFs are supported."
        )
    return "\n".join(pages)


def detect_report_type(text: str) -> str:
    lower = text.lower()
    for report_type, keywords in _REPORT_TYPE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return report_type
    return "lab"
