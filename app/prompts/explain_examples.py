"""Few-shot example responses for the explain agent, split out to keep explain.py under 150 lines."""

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
_PNEUMONIA_DX_EXPLANATION = (
    "You were treated in hospital for a lung infection called pneumonia. "
    "Pneumonia is an infection that inflames the air sacs in the lungs. "
    "You have been sent home with antibiotics to complete your treatment."
)
_AMOXICILLIN_EXPLANATION = (
    "Amoxicillin is an antibiotic used to treat bacterial infections like pneumonia. "
    "Take the full course even if you feel better, to make sure the infection clears completely."
)
_FOLLOWUP_EXPLANATION = (
    "Your doctor has asked you to attend a follow-up appointment to check your recovery. "
    "This is routine after a hospital admission and gives your doctor a chance to review "
    "your progress and answer any questions."
)
_ER_EXPLANATION = (
    "The tumour cells in your biopsy responded positively to oestrogen. "
    "This is an important piece of information because it means the cancer may respond well "
    "to hormone-blocking treatments, which your specialist will discuss with you."
)
_GRADE_EXPLANATION = (
    "The grade describes how different the cancer cells look compared to normal cells. "
    "Grade 2 means the cells look moderately abnormal — not the slowest-growing (grade 1) "
    "nor the fastest-growing (grade 3). Your specialist will use this alongside other results "
    "to plan your treatment."
)
_MARGINS_EXPLANATION = (
    "Clear margins means the surgeon removed the tumour with a rim of healthy tissue around it. "
    "This is a good result — it reduces the chance that any cancer cells were left behind."
)

CBC_RESPONSE = (
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

RADIOLOGY_RESPONSE = (
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

DISCHARGE_RESPONSE = (
    '{\n'
    '  "findings": [\n'
    '    {\n'
    '      "name": "Discharge Diagnosis",\n'
    '      "value": "Community-acquired pneumonia",\n'
    '      "unit": "",\n'
    '      "reference_range": "No active infection expected",\n'
    f'      "plain_explanation": "{_PNEUMONIA_DX_EXPLANATION}",\n'
    '      "confidence": 0.97\n'
    '    },\n'
    '    {\n'
    '      "name": "Medication: Amoxicillin",\n'
    '      "value": "500 mg three times daily for 7 days",\n'
    '      "unit": "",\n'
    '      "reference_range": "As prescribed",\n'
    f'      "plain_explanation": "{_AMOXICILLIN_EXPLANATION}",\n'
    '      "confidence": 0.99\n'
    '    },\n'
    '    {\n'
    '      "name": "Follow-up",\n'
    '      "value": "GP appointment in 1 week",\n'
    '      "unit": "",\n'
    '      "reference_range": "As scheduled",\n'
    f'      "plain_explanation": "{_FOLLOWUP_EXPLANATION}",\n'
    '      "confidence": 0.95\n'
    '    }\n'
    '  ]\n'
    '}'
)

PATHOLOGY_RESPONSE = (
    '{\n'
    '  "findings": [\n'
    '    {\n'
    '      "name": "Oestrogen Receptor (ER) Status",\n'
    '      "value": "POSITIVE (90%)",\n'
    '      "unit": "",\n'
    '      "reference_range": "Negative expected",\n'
    f'      "plain_explanation": "{_ER_EXPLANATION}",\n'
    '      "confidence": 0.97\n'
    '    },\n'
    '    {\n'
    '      "name": "Tumour Grade",\n'
    '      "value": "Grade 2 of 3",\n'
    '      "unit": "",\n'
    '      "reference_range": "Grade 1 expected (well-differentiated)",\n'
    f'      "plain_explanation": "{_GRADE_EXPLANATION}",\n'
    '      "confidence": 0.95\n'
    '    },\n'
    '    {\n'
    '      "name": "Surgical Margins",\n'
    '      "value": "Clear (>3 mm)",\n'
    '      "unit": "",\n'
    '      "reference_range": "Clear margins expected",\n'
    f'      "plain_explanation": "{_MARGINS_EXPLANATION}",\n'
    '      "confidence": 0.98\n'
    '    }\n'
    '  ]\n'
    '}'
)
