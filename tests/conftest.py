import pytest


@pytest.fixture
def sample_cbc_text() -> str:
    return """
CBC Blood Panel Report
Patient Name: John Smith
Date of Birth: 01/01/1980
MRN: 12345678
Phone: 555-123-4567

Haemoglobin: 10.2 g/dL (Reference: 12.0-16.0 g/dL)
MCV: 72 fL (Reference: 80-100 fL)
WBC: 6.2 x10^3/uL (Reference: 4.5-11.0 x10^3/uL)
"""


@pytest.fixture
def sample_radiology_text() -> str:
    return """
Radiology Report
Patient: Jane Doe
DOB: 1975-03-15
NHS Number: 123 456 7890

FINDINGS: Mild consolidation in the right lower lobe.
IMPRESSION: Findings consistent with early pneumonia.
"""
