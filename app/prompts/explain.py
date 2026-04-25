SYSTEM_PROMPT = """You are analysing a de-identified medical report. Do not attempt to
re-identify the patient. Do not provide a diagnosis. Explain findings clearly for a
non-medical audience.

Return a JSON object with a "findings" array. Each finding must have:
- "name": the test or measurement name
- "value": the measured value with unit (e.g. "9.2 g/dL", "POSITIVE", "78 %")
- "unit": the unit alone (empty string for qualitative results like POSITIVE/NEGATIVE)
- "reference_range": the normal range string. For qualitative tests use "Negative expected"
  or "Not detected expected". For numeric tests use the format "low – high unit".
- "plain_explanation": a clear explanation in plain English, maximum 3 sentences, no medical jargon
- "confidence": a float between 0.0 and 1.0

IMPORTANT: Include ALL findings from the report — numeric AND qualitative (e.g. POSITIVE
malaria tests, culture results, RDT results). Do not omit any finding flagged as HIGH, LOW,
or POSITIVE in the source document.

Return ONLY valid JSON. No markdown, no prose outside the JSON."""

_HAEMO_EXPLANATION = (
    "Your haemoglobin is slightly below the normal range. "
    "Haemoglobin is the protein in red blood cells that carries oxygen around your body. "
    "A low level can cause tiredness and dizziness, which may suggest mild anaemia."
)
_WBC_EXPLANATION = (
    "Your white blood cell count is within the normal range. "
    "White blood cells are part of your immune system and help fight infections. "
    "This result suggests your immune system is functioning normally."
)
_CONSOLIDATION_EXPLANATION = (
    "The X-ray shows a small area of the lower right lung that appears more dense than normal. "
    "This pattern is often caused by fluid or infection filling the tiny air sacs in the lung. "
    "Your doctor's summary suggests this may be an early lung infection."
)

_CBC_RESPONSE = (
    '{\n'
    '  "findings": [\n'
    '    {\n'
    '      "name": "Haemoglobin",\n'
    '      "value": "10.2 g/dL",\n'
    '      "unit": "g/dL",\n'
    '      "reference_range": "12.0-16.0 g/dL",\n'
    f'      "plain_explanation": "{_HAEMO_EXPLANATION}",\n'
    '      "confidence": 0.95\n'
    '    },\n'
    '    {\n'
    '      "name": "WBC",\n'
    '      "value": "6.2 x10^3/uL",\n'
    '      "unit": "x10^3/uL",\n'
    '      "reference_range": "4.5-11.0 x10^3/uL",\n'
    f'      "plain_explanation": "{_WBC_EXPLANATION}",\n'
    '      "confidence": 0.98\n'
    '    }\n'
    '  ]\n'
    '}'
)

_RADIOLOGY_RESPONSE = (
    '{\n'
    '  "findings": [\n'
    '    {\n'
    '      "name": "Right Lower Lobe Consolidation",\n'
    '      "value": "Mild",\n'
    '      "unit": "",\n'
    '      "reference_range": "No consolidation expected",\n'
    f'      "plain_explanation": "{_CONSOLIDATION_EXPLANATION}",\n'
    '      "confidence": 0.88\n'
    '    }\n'
    '  ]\n'
    '}'
)

FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": (
            "Analyse this CBC lab report:\n"
            "Haemoglobin: 10.2 g/dL (Reference: 12.0-16.0 g/dL)\n"
            "WBC: 6.2 x10^3/uL (Reference: 4.5-11.0 x10^3/uL)"
        ),
    },
    {
        "role": "assistant",
        "content": _CBC_RESPONSE,
    },
    {
        "role": "user",
        "content": (
            "Analyse this radiology report:\n"
            "FINDINGS: Mild consolidation in the right lower lobe."
            " Cardiac silhouette within normal limits.\n"
            "IMPRESSION: Findings consistent with early pneumonia."
        ),
    },
    {
        "role": "assistant",
        "content": _RADIOLOGY_RESPONSE,
    },
]


def build_explain_messages(deid_text: str, report_type: str) -> list[dict[str, str]]:
    messages = list(FEW_SHOT_EXAMPLES)
    messages.append({
        "role": "user",
        "content": f"Analyse this {report_type} report:\n\n{deid_text}",
    })
    return messages
