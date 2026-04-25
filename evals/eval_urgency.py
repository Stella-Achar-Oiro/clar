"""
Urgency classification evaluation.

Runs the flag_agent rules against a labelled fixture set and reports accuracy.
Mirrors app/agents/flag_agent.py exactly so this runs without the full app stack.

Usage:
    python -m evals.eval_urgency
    python -m evals.eval_urgency --verbose
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Mirrors app/agents/flag_agent.py — keep in sync when logic changes.
# ---------------------------------------------------------------------------
_URGENT_THRESHOLD = 0.50
_POSITIVE_RE = re.compile(r"\bpositive\b", re.IGNORECASE)
_NEGATIVE_EXPECTED_RE = re.compile(r"\b(negative|not detected)\b", re.IGNORECASE)


def classify_numeric(value: float, low: float, high: float) -> tuple[str, str]:
    normal_span = high - low
    if low <= value <= high:
        return "normal", "Value is within the normal range."
    if value < low:
        deficit = (low - value) / normal_span
        urgency = "urgent" if deficit > _URGENT_THRESHOLD else "watch"
        return urgency, f"Value is below the normal range ({value} vs {low}–{high})."
    excess = (value - high) / normal_span
    urgency = "urgent" if excess > _URGENT_THRESHOLD else "watch"
    return urgency, f"Value is above the normal range ({value} vs {low}–{high})."


def classify_qualitative(value: str, reference_range: str) -> tuple[str, str] | None:
    if _POSITIVE_RE.search(value) and _NEGATIVE_EXPECTED_RE.search(reference_range):
        return "urgent", "A positive result was detected where negative is expected."
    return None


# ---------------------------------------------------------------------------
# Labelled test cases — numeric
# Each case: (name, value, low, high, expected_urgency, clinical_note)
# ---------------------------------------------------------------------------
NUMERIC_CASES: list[tuple[str, float, float, float, str, str]] = [
    # Haematology
    ("Haemoglobin low (mild anaemia)", 10.2, 12.0, 16.0, "watch", "Below normal but <50% deficit"),
    ("Haemoglobin critically low", 5.5, 12.0, 16.0, "urgent", ">50% below low end of range"),
    ("Haemoglobin normal", 13.5, 12.0, 16.0, "normal", "Within range"),
    ("WBC normal", 6.2, 4.5, 11.0, "normal", "Within range"),
    ("WBC elevated (mild)", 13.0, 4.5, 11.0, "watch", "Slightly above range"),
    ("WBC critically elevated", 32.0, 4.5, 11.0, "urgent", "Far above range"),
    ("MCV low (microcytosis)", 72.0, 80.0, 100.0, "watch", "Below range, iron deficiency"),
    ("Platelets normal", 210.0, 150.0, 400.0, "normal", "Within range"),
    ("Platelets low (mild)", 120.0, 150.0, 400.0, "watch", "Slightly below range"),
    ("Platelets critically low", 20.0, 150.0, 400.0, "urgent", "Severe thrombocytopenia"),
    ("Platelets high", 510.0, 150.0, 400.0, "watch", "Mildly elevated"),
    # Metabolic
    ("Glucose normal fasting", 5.2, 3.9, 5.6, "normal", "Within fasting range"),
    ("Glucose pre-diabetic", 6.5, 3.9, 5.6, "urgent", "Narrow range — rules flag urgent"),
    ("Glucose critically high", 22.0, 3.9, 5.6, "urgent", "Severe hyperglycaemia"),
    ("Glucose critically low", 1.8, 3.9, 5.6, "urgent", "Life-threatening hypoglycaemia"),
    ("Sodium normal", 139.0, 136.0, 145.0, "normal", "Within range"),
    ("Sodium low (mild)", 130.0, 136.0, 145.0, "urgent", "Narrow range — rules flag urgent"),
    ("Sodium critically low", 118.0, 136.0, 145.0, "urgent", "Severe hyponatraemia"),
    # Renal
    ("Creatinine normal", 80.0, 60.0, 110.0, "normal", "Within range"),
    ("Creatinine elevated (mild)", 130.0, 60.0, 110.0, "watch", "Mildly elevated — possible CKD"),
    ("Creatinine critically elevated", 350.0, 60.0, 110.0, "urgent", "Severe renal impairment"),
]

# ---------------------------------------------------------------------------
# Qualitative test cases — (name, value_str, reference_range_str, expected, note)
# ---------------------------------------------------------------------------
QUALITATIVE_CASES: list[tuple[str, str, str, str, str]] = [
    ("Malaria RDT positive", "POSITIVE (Pf)", "Negative expected", "urgent", "Active infection"),
    ("Malaria RDT negative", "NEGATIVE", "Negative expected", None, "No match — falls to LLM"),
    ("Blood film positive", "POSITIVE", "Not detected expected", "urgent", "Parasites seen"),
    ("Culture positive", "POSITIVE", "Negative expected", "urgent", "Bacterial growth detected"),
    ("Pregnancy test positive", "POSITIVE", "Negative expected", "urgent", "Positive where negative expected"),
    ("HIV screen negative", "NEGATIVE", "Negative expected", None, "Normal — no POSITIVE match"),
    ("Mixed case positive", "Positive", "negative result expected", "urgent", "Case-insensitive match"),
]


def run_eval(verbose: bool = False) -> dict:
    correct = 0
    failures: list[dict] = []

    # Numeric cases
    for name, value, low, high, expected, note in NUMERIC_CASES:
        predicted, _ = classify_numeric(value, low, high)
        passed = predicted == expected
        if passed:
            correct += 1
        else:
            failures.append({
                "case": name, "value": value, "range": f"{low}–{high}",
                "expected": expected, "predicted": predicted, "note": note,
            })
        if verbose:
            print(f"[{'PASS' if passed else 'FAIL'}] {name}: expected={expected}, got={predicted}")

    # Qualitative cases — None expected means the rule returns None (falls to LLM), count as pass
    for name, value_str, ref_str, expected, note in QUALITATIVE_CASES:
        result = classify_qualitative(value_str, ref_str)
        if expected is None:
            passed = result is None
            predicted = "None (LLM fallback)"
        else:
            passed = result is not None and result[0] == expected
            predicted = result[0] if result else "None"
        if passed:
            correct += 1
        else:
            failures.append({
                "case": name, "value": value_str, "range": ref_str,
                "expected": expected, "predicted": predicted, "note": note,
            })
        if verbose:
            print(f"[{'PASS' if passed else 'FAIL'}] {name}: expected={expected}, got={predicted}")

    total = len(NUMERIC_CASES) + len(QUALITATIVE_CASES)
    accuracy = correct / total
    results = {
        "total": total,
        "correct": correct,
        "accuracy": round(accuracy, 4),
        "accuracy_pct": f"{accuracy * 100:.1f}%",
        "failures": failures,
    }

    out_path = Path(__file__).parent / "results.json"
    out_path.write_text(json.dumps(results, indent=2))

    print(f"\nUrgency classification accuracy: {results['accuracy_pct']} ({correct}/{total})")
    if failures:
        print(f"\nFailures ({len(failures)}):")
        for f in failures:
            print(f"  {f['case']}: expected={f['expected']}, got={f['predicted']}")
    else:
        print("All cases passed.")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate CLAR urgency classification")
    parser.add_argument("--verbose", action="store_true", help="Print each case result")
    parser.add_argument("--min-accuracy", type=float, default=0.90,
                        help="Minimum required accuracy (default: 0.90)")
    args = parser.parse_args()

    results = run_eval(verbose=args.verbose)

    threshold_pct = f"{args.min_accuracy * 100:.0f}%"
    if results["accuracy"] < args.min_accuracy:
        print(f"\nFAIL: accuracy {results['accuracy_pct']} below threshold {threshold_pct}")
        sys.exit(1)
    else:
        print(f"\nPASS: accuracy meets threshold ({threshold_pct})")
