from pathlib import Path
from app.models.report import CLARState
from app.services.extractor import extract_text, detect_report_type


def run_extract_agent(state: CLARState, file_path: Path) -> CLARState:
    raw_text = extract_text(file_path)
    report_type = detect_report_type(raw_text)
    return {**state, "raw_text": raw_text, "report_type": report_type}
