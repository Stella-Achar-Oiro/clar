from pathlib import Path

import pytest

from app.services.extractor import detect_report_type, extract_text

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_extract_txt_returns_text():
    text = extract_text(FIXTURES / "sample_cbc.txt")
    assert "Haemoglobin" in text
    assert len(text) > 50


def test_detect_lab_report_type():
    text = "CBC Blood Panel Report\nHaemoglobin: 10.2 g/dL"
    assert detect_report_type(text) == "lab"


def test_detect_radiology_report_type():
    text = "Radiology Report\nChest X-Ray PA\nFINDINGS: consolidation"
    assert detect_report_type(text) == "radiology"


def test_detect_pathology_report_type():
    text = "Pathology Report\nBiopsy specimen received"
    assert detect_report_type(text) == "pathology"


def test_detect_discharge_report_type():
    text = "Discharge Summary\nPatient discharged in stable condition"
    assert detect_report_type(text) == "discharge"


def test_detect_unknown_defaults_to_lab():
    text = "Some medical document with no clear type indicator"
    assert detect_report_type(text) == "lab"


def test_extract_nonexistent_file_raises():
    with pytest.raises(FileNotFoundError):
        extract_text(Path("/nonexistent/file.txt"))
