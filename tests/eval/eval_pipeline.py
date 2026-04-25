"""
Evaluation harness — runs full pipeline on fixtures and logs to LangSmith.
Run manually: python -m tests.eval.eval_pipeline
Not part of pytest suite (no test_ prefix on functions).
"""
import os
from pathlib import Path
from app.agents.pipeline import run_pipeline

FIXTURES = Path(__file__).parent.parent / "fixtures"

SCENARIOS = [
    {"file": FIXTURES / "sample_cbc.txt", "expected_report_type": "lab", "expected_min_findings": 1},
    {"file": FIXTURES / "sample_radiology.txt", "expected_report_type": "radiology", "expected_min_findings": 1},
]


def evaluate() -> None:
    results = []
    for scenario in SCENARIOS:
        print(f"\nEvaluating: {scenario['file'].name}")
        state = run_pipeline(scenario["file"])
        passed = (
            state["report_type"] == scenario["expected_report_type"]
            and len(state["explanations"]) >= scenario["expected_min_findings"]
            and len(state["questions"]) == 5
            and state["error"] is None
        )
        results.append({
            "file": scenario["file"].name,
            "passed": passed,
            "report_type": state["report_type"],
            "finding_count": len(state["explanations"]),
            "question_count": len(state["questions"]),
            "error": state.get("error"),
        })
        print(f"  {'PASS' if passed else 'FAIL'} — {state['report_type']}, "
              f"{len(state['explanations'])} findings, {len(state['questions'])} questions")

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    print(f"\nResults: {passed_count}/{total} passed")


if __name__ == "__main__":
    evaluate()
