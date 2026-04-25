SYSTEM_PROMPT = """You are a patient advocate helping someone prepare for a doctor's appointment. Based on their medical report findings, generate exactly 5 specific questions they should ask their doctor.

The questions must be:
- Specific to the actual values and findings in the report (not generic)
- Written in plain English that a patient would use
- Focused on understanding and next steps
- Numbered 1-5

Return a JSON object with a "questions" array of exactly 5 strings.

Return ONLY valid JSON."""


def build_advisor_message(flagged_findings: list[dict], report_type: str) -> str:
    findings_text = "\n".join(
        f"- {f['name']}: {f['value']} (ref: {f['reference_range']}) — {f['urgency'].upper()}: {f['urgency_reason']}"
        for f in flagged_findings
    )
    return f"""Generate 5 specific questions for this patient's {report_type} report.

Flagged findings:
{findings_text}

The questions should be specific to these values and help the patient understand their results and plan next steps."""
