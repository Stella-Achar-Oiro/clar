import time

from loguru import logger

from app.models.report import CLARState
from app.observability.metrics import AGENT_DURATION
from app.prompts.explain import SYSTEM_PROMPT, build_explain_messages
from app.services.llm import call_llm


def run_explain_agent(state: CLARState) -> CLARState:
    start = time.time()
    try:
        messages = build_explain_messages(state["deid_text"], state["report_type"])
        result = call_llm(
            system=SYSTEM_PROMPT,
            messages=messages,
            temperature=0.1,
            max_tokens=2000,
            agent_name="explain",
        )
        explanations = result.get("findings", [])
        logger.debug("explain_agent_complete", finding_count=len(explanations))
        return {**state, "explanations": explanations, "error": None}
    except Exception as exc:
        logger.error("explain_agent_failed", error=str(exc))
        return {**state, "explanations": [], "error": f"explain_failed: {exc}"}
    finally:
        AGENT_DURATION.labels(agent_name="explain").observe(time.time() - start)
