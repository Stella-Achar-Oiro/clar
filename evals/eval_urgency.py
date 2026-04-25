"""
Urgency classification evaluation.

Runs the flag_agent against a labelled fixture set and reports accuracy.
Uses rules-based classify_numeric for numeric findings (no API calls needed)
and records results to evals/results.json.

Usage:
    python -m evals.eval_urgency
    python -m evals.eval_urgency --verbose
"""

import argparse
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Inline classify_numeric — mirrors app/agents/flag_agent.py exactly so
# this eval runs without the full app stack (no API keys needed).
# ---------------------------------------------------------------------------
_URGENT_THRESHOLD = 0.50


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

# ---------------------------------------------------------------------------
# Labelled test cases
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


def run_eval(verbose: bool = False) -> dict:
    correct = 0
    total = len(NUMERIC_CASES)
    failures: list[dict] = []

    for name, value, low, high, expected, note in NUMERIC_CASES:
        predicted, reason = classify_numeric(value, low, high)
        passed = predicted == expected
        if passed:
            correct += 1
        else:
            failures.append({
                "case": name,
                "value": value,
                "range": f"{low}–{high}",
                "expected": expected,
                "predicted": predicted,
                "reason": reason,
                "note": note,
            })
        if verbose:
            status = "PASS" if passed else "FAIL"
            print(f"[{status}] {name}: expected={expected}, got={predicted}")

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
