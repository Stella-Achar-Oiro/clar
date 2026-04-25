SYSTEM_PROMPT = """You are analysing a de-identified medical report. Do not attempt to re-identify the patient. Do not provide a diagnosis. Explain findings clearly for a non-medical audience.

Return a JSON object with a "findings" array. Each finding must have:
- "name": the test or measurement name
- "value": the measured value with unit
- "unit": the unit alone
- "reference_range": the normal range string
- "plain_explanation": a clear explanation in plain English, maximum 3 sentences, no medical jargon
- "confidence": a float between 0.0 and 1.0

Return ONLY valid JSON. No markdown, no prose outside the JSON."""

FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": """Analyse this CBC lab report:
Haemoglobin: 10.2 g/dL (Reference: 12.0-16.0 g/dL)
WBC: 6.2 x10^3/uL (Reference: 4.5-11.0 x10^3/uL)""",
    },
    {
        "role": "assistant",
        "content": """{
  "findings": [
    {
      "name": "Haemoglobin",
      "value": "10.2 g/dL",
      "unit": "g/dL",
      "reference_range": "12.0-16.0 g/dL",
      "plain_explanation": "Your haemoglobin is slightly below the normal range. Haemoglobin is the protein in red blood cells that carries oxygen around your body. A low level can cause tiredness and dizziness, which may suggest mild anaemia.",
      "confidence": 0.95
    },
    {
      "name": "WBC",
      "value": "6.2 x10^3/uL",
      "unit": "x10^3/uL",
      "reference_range": "4.5-11.0 x10^3/uL",
      "plain_explanation": "Your white blood cell count is within the normal range. White blood cells are part of your immune system and help fight infections. This result suggests your immune system is functioning normally.",
      "confidence": 0.98
    }
  ]
}""",
    },
    {
        "role": "user",
        "content": """Analyse this radiology report:
FINDINGS: Mild consolidation in the right lower lobe. Cardiac silhouette within normal limits.
IMPRESSION: Findings consistent with early pneumonia.""",
    },
    {
        "role": "assistant",
        "content": """{
  "findings": [
    {
      "name": "Right Lower Lobe Consolidation",
      "value": "Mild",
      "unit": "",
      "reference_range": "No consolidation expected",
      "plain_explanation": "The X-ray shows a small area of the lower right lung that appears more dense than normal. This pattern is often caused by fluid or infection filling the tiny air sacs in the lung. Your doctor's summary suggests this may be an early lung infection.",
      "confidence": 0.88
    }
  ]
}""",
    },
]


def build_explain_messages(deid_text: str, report_type: str) -> list[dict]:
    messages = list(FEW_SHOT_EXAMPLES)
    messages.append({
        "role": "user",
        "content": f"Analyse this {report_type} report:\n\n{deid_text}",
    })
    return messages
