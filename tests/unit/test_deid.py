import pytest
from app.services.deid import deidentify

# Known PII strings that MUST NOT appear in de-identified output
PATIENT_NAME = "John Smith"
DOB = "01/01/1980"
PHONE = "555-123-4567"
EMAIL = "john.smith@example.com"
NHS_NUMBER = "943 476 5919"
MRN = "MRN: 12345678"
SSN = "123-45-6789"

SAMPLE_TEXT = f"""
CBC Blood Panel Report
Patient Name: {PATIENT_NAME}
Date of Birth: {DOB}
Phone: {PHONE}
Email: {EMAIL}
NHS Number: {NHS_NUMBER}
{MRN}
SSN: {SSN}

Haemoglobin: 10.2 g/dL (Reference: 12.0-16.0 g/dL)
WBC: 6.2 x10^3/uL (Reference: 4.5-11.0 x10^3/uL)
"""


def test_patient_name_removed():
    deid_text, _, failed = deidentify(SAMPLE_TEXT)
    assert PATIENT_NAME not in deid_text
    assert not failed


def test_date_removed():
    deid_text, _, failed = deidentify(SAMPLE_TEXT)
    assert DOB not in deid_text
    assert not failed


def test_phone_removed():
    deid_text, _, failed = deidentify(SAMPLE_TEXT)
    assert PHONE not in deid_text
    assert not failed


def test_email_removed():
    deid_text, _, failed = deidentify(SAMPLE_TEXT)
    assert EMAIL not in deid_text
    assert not failed


def test_nhs_number_removed():
    deid_text, _, failed = deidentify(SAMPLE_TEXT)
    assert NHS_NUMBER not in deid_text
    assert not failed


def test_mrn_removed():
    deid_text, _, failed = deidentify(SAMPLE_TEXT)
    assert "12345678" not in deid_text
    assert not failed


def test_ssn_removed():
    deid_text, _, failed = deidentify(SAMPLE_TEXT)
    assert SSN not in deid_text
    assert not failed


def test_entities_list_non_empty():
    _, entities, failed = deidentify(SAMPLE_TEXT)
    assert len(entities) > 0
    assert not failed


def test_medical_content_preserved():
    deid_text, _, _ = deidentify(SAMPLE_TEXT)
    assert "Haemoglobin" in deid_text
    assert "10.2 g/dL" in deid_text


def test_deid_failed_false_on_success():
    _, _, failed = deidentify(SAMPLE_TEXT)
    assert failed is False


def test_empty_text_returns_deid_failed():
    _, _, failed = deidentify("")
    assert failed is True


def test_entity_list_has_type_and_count():
    _, entities, _ = deidentify(SAMPLE_TEXT)
    for entity in entities:
        assert "type" in entity
        assert "count" in entity
