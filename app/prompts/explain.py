from app.prompts.explain_examples import (
    CBC_RESPONSE,
    DISCHARGE_RESPONSE,
    PATHOLOGY_RESPONSE,
    RADIOLOGY_RESPONSE,
)

SYSTEM_PROMPT = """You are analysing a de-identified medical report. Do not attempt to
re-identify the patient. Do not provide a diagnosis. Explain findings clearly for a
non-medical audience.

Return a JSON object with a "findings" array. Each finding must have:
- "name": the test or measurement name
- "value": the measured value with unit (e.g. "9.2 g/dL", "POSITIVE", "78 %")
- "unit": the unit alone (empty string for qualitative results like POSITIVE/NEGATIVE)
- "reference_range": the normal range string. For qualitative tests use "Negative expected"
  or "Not detected expected". For numeric tests use the format "low – high unit".
  For discharge findings use "No active infection expected", "As prescribed", "As scheduled".
  For pathology use "Negative expected", "Clear margins expected", "Grade 1 expected".
- "plain_explanation": a clear explanation in plain English, maximum 3 sentences, no medical jargon
- "confidence": a float between 0.0 and 1.0

IMPORTANT: Include ALL findings from the report — numeric AND qualitative (e.g. POSITIVE
malaria tests, culture results, RDT results, discharge diagnoses, medications, pathology grades).
Do not omit any finding flagged as HIGH, LOW, POSITIVE, or abnormal in the source document.

Return ONLY valid JSON. No markdown, no prose outside the JSON."""

FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": (
            "Analyse this CBC lab report:\n"
            "Haemoglobin: 10.2 g/dL (Reference: 12.0-16.0 g/dL)\n"
            "WBC: 6.2 x10^3/uL (Reference: 4.5-11.0 x10^3/uL)"
        ),
    },
    {"role": "assistant", "content": CBC_RESPONSE},
    {
        "role": "user",
        "content": (
            "Analyse this radiology report:\n"
            "FINDINGS: Mild consolidation in the right lower lobe."
            " Cardiac silhouette within normal limits.\n"
            "IMPRESSION: Findings consistent with early pneumonia."
        ),
    },
    {"role": "assistant", "content": RADIOLOGY_RESPONSE},
    {
        "role": "user",
        "content": (
            "Analyse this discharge report:\n"
            "DISCHARGE DIAGNOSIS: Community-acquired pneumonia\n"
            "MEDICATIONS ON DISCHARGE: Amoxicillin 500 mg TDS for 7 days\n"
            "FOLLOW-UP: GP in 1 week"
        ),
    },
    {"role": "assistant", "content": DISCHARGE_RESPONSE},
    {
        "role": "user",
        "content": (
            "Analyse this pathology report:\n"
            "SPECIMEN: Right breast core biopsy\n"
            "ER Status: Positive (90%)\n"
            "Tumour Grade: 2/3 (Nottingham)\n"
            "Surgical Margins: Clear (>3 mm)"
        ),
    },
    {"role": "assistant", "content": PATHOLOGY_RESPONSE},
]


def build_explain_messages(deid_text: str, report_type: str) -> list[dict[str, str]]:
    messages = list(FEW_SHOT_EXAMPLES)
    messages.append({
        "role": "user",
        "content": f"Analyse this {report_type} report:\n\n{deid_text}",
    })
    return messages
