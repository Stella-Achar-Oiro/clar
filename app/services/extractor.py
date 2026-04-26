from pathlib import Path

import pdfplumber

# Priority order matters: more specific types first to avoid false matches.
# "findings:" and "impression:" removed from radiology — they appear in all report types.
_REPORT_TYPE_KEYWORDS: dict[str, list[str]] = {
    "discharge": [
        "discharge summary", "discharge diagnosis", "discharge date",
        "admission date", "discharged on", "plan on discharge",
        "medications on discharge", "follow-up appointment",
    ],
    "pathology": [
        "pathology report", "histopathology", "biopsy", "histology",
        "microscopic description", "gross description",
        "tumour grade", "tumor grade", "surgical margins", "receptor status",
    ],
    "radiology": [
        "radiology", "x-ray", "xray", "mri", "ct scan", "ct of",
        "ultrasound", "echocardiogram", "echo report", "pet scan",
        "nuclear medicine", "doppler", "imaging report",
    ],
    "lab": [
        "cbc", "full blood count", "fbc", "blood panel",
        "haemoglobin", "hemoglobin", "glucose", "creatinine",
        "laboratory", "lab results", "lipid profile", "hba1c",
        "thyroid function", "liver function", "renal function",
        "urine culture", "blood culture", "egfr",
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

            # Also extract free text — discharge/radiology pages mix tables with narrative.
            # deduplicate against table content by only adding if text adds new lines.
            text = page.extract_text()
            if text:
                table_content = " ".join(parts)
                for line in text.splitlines():
                    if line.strip() and line.strip() not in table_content:
                        parts.append(line)

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
