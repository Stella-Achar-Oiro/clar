# POST /report

Analyse a medical report document.

## Request

```
POST /report
Content-Type: multipart/form-data
```

### Form fields

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | Yes | The report document. PDF, PNG, JPG, JPEG, or TIFF. Max 10 MB. |

### Example (curl)

```bash
curl -X POST https://<base-url>/report \
  -F "file=@blood_test.pdf"
```

## Response

```
200 OK
Content-Type: application/json
```

```json
{
  "report_id": "rpt_01j...",
  "report_type": "lab",
  "verdict": {
    "level": "watch",
    "summary": "Most results are normal. One value is mildly outside range."
  },
  "findings": [
    {
      "name": "Haemoglobin",
      "plain_explanation": "Your haemoglobin level is within the normal range.",
      "value": "14.2 g/dL",
      "reference_range": "13.5–17.5 g/dL",
      "urgency": "normal"
    }
  ],
  "questions": [
    "Should I be concerned about my slightly elevated white blood cell count?",
    "Does my cholesterol result mean I need to make dietary changes?"
  ],
  "processing_time_ms": 4821,
  "deid_entities_removed": 3
}
```

### Response fields

| Field | Type | Description |
|---|---|---|
| `report_id` | string | Unique identifier for this report, used in chat requests |
| `report_type` | string | Detected type: `lab`, `radiology`, or `discharge` |
| `verdict.level` | string | Overall urgency: `normal`, `watch`, `concern`, or `urgent` |
| `verdict.summary` | string | One-sentence plain-English summary of the overall result |
| `findings` | array | Structured findings extracted from the report |
| `findings[].urgency` | string | Per-finding urgency: `normal`, `watch`, `concern`, or `urgent` |
| `questions` | array | Suggested questions to ask a doctor |
| `processing_time_ms` | integer | End-to-end processing time in milliseconds |
| `deid_entities_removed` | integer | Number of personal identifiers removed before analysis |

## Error responses

| Status | Condition |
|---|---|
| 400 | File type not supported or file too large |
| 500 | Processing failed (LLM or extraction error) |
