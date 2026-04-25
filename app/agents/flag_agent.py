import re
import time
from app.models.report import CLARState
from app.services.llm import call_llm
from app.prompts.flag import SYSTEM_PROMPT, build_flag_message
from app.observability.metrics import AGENT_DURATION
from loguru import logger

_RANGE_RE = re.compile(r"([\d.]+)\s*[-–]\s*([\d.]+)")
_VALUE_RE = re.compile(r"([\d.]+)")

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


def _try_rules(finding: dict) -> tuple[str, str] | None:
    range_match = _RANGE_RE.search(finding.get("reference_range", ""))
    value_match = _VALUE_RE.search(finding.get("value", ""))
    if not range_match or not value_match:
        return None
    try:
        val = float(value_match.group(1))
        low = float(range_match.group(1))
        high = float(range_match.group(2))
        return classify_numeric(val, low, high)
    except ValueError:
        return None


def _llm_fallback(finding: dict) -> tuple[str, str]:
    msg = build_flag_message(
        name=finding["name"],
        value=finding["value"],
        reference_range=finding.get("reference_range", ""),
        plain_explanation=finding.get("plain_explanation", ""),
    )
    result = call_llm(
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": msg}],
        temperature=0.1,
        max_tokens=1000,
        agent_name="flag",
    )
    return result["urgency"], result["urgency_reason"]


def run_flag_agent(state: CLARState) -> CLARState:
    start = time.time()
    flagged: list[dict] = []
    for finding in state["explanations"]:
        rules_result = _try_rules(finding)
        if rules_result:
            urgency, reason = rules_result
        else:
            urgency, reason = _llm_fallback(finding)
        flagged.append({**finding, "urgency": urgency, "urgency_reason": reason})
        logger.debug("flag_agent_finding", name=finding["name"], urgency=urgency)
    AGENT_DURATION.labels(agent_name="flag").observe(time.time() - start)
    return {**state, "flagged": flagged}
