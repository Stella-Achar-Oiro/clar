SYSTEM_PROMPT = """You are a medical report urgency classifier.
Think step by step before classifying.

You will receive a finding with a value and reference range. Classify the urgency as:
- "normal": value is within the reference range
- "watch": value is outside the reference range but not critically so
- "urgent": value is critically outside the normal range and requires prompt medical attention

Return a JSON object with:
- "urgency": "normal" | "watch" | "urgent"
- "urgency_reason": a brief plain-English explanation (1 sentence)

Return ONLY valid JSON."""


def build_flag_message(name: str, value: str, reference_range: str, plain_explanation: str) -> str:
    return f"""Classify the urgency of this finding:
Name: {name}
Value: {value}
Reference range: {reference_range}
Context: {plain_explanation}

Think step by step: Is the value within range? If outside, how far outside?
Is this clinically significant?"""
